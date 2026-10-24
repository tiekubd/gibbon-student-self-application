<?php
/*
 * Online invoice payment receipts (GibbonEdu/core#2201), checked against Gibbon's own receiptContents().
 *
 * Creates two paid test invoices for an enrolled student, adds online payments to them, and builds each
 * receipt the way invoices_payOnlineProcess.php does: first with the stock receipt number (old), then
 * with the fixed one (new). Removes everything it created at the end.
 *
 * Test site only. Run from anywhere:
 *   GIBBON_ROOT=/path/to/gibbon php receipt_test.php
 *
 * Expected:
 *   old: a logged-in payer gets a blank status and "no records"; a second payment by someone not
 *        logged in gets receipt 1 (the first payment) again.
 *   new: every receipt has the right number, status and payment.
 */

$root = getenv('GIBBON_ROOT') ?: die("Set GIBBON_ROOT to the Gibbon webroot.\n");
chdir($root);
$_SERVER['HTTP_HOST'] = $_SERVER['HTTP_HOST'] ?? 'localhost';
$_SERVER['REQUEST_URI'] = '/';
require $root.'/gibbon.php';
require_once $root.'/modules/Finance/moduleFunctions.php';

$pdo = $connection2;
$year = $pdo->query("SELECT gibbonSchoolYearID FROM gibbonSchoolYear WHERE status='Current'")->fetchColumn();
$student = $pdo->query("SELECT gibbonPersonID FROM gibbonStudentEnrolment WHERE gibbonSchoolYearID=$year LIMIT 1")->fetchColumn();
if (!$student) die("No enrolled student in the current school year.\n");

$pdo->exec("INSERT INTO gibbonFinanceInvoicee (gibbonPersonID, invoiceTo, companyName, companyContact, companyEmail, companyAll) VALUES ($student, 'Company', 'Receipt Test', 'Receipt Test', 'receipt-test@example.com', 'Y')");
$invoicee = $pdo->lastInsertId();
$category = $pdo->query("SELECT gibbonFinanceFeeCategoryID FROM gibbonFinanceFeeCategory ORDER BY gibbonFinanceFeeCategoryID LIMIT 1")->fetchColumn();

$invoices = [];
foreach (['logged in' => 1, 'not logged in' => null] as $who => $personID) {
    $pdo->exec("INSERT INTO gibbonFinanceInvoice (gibbonSchoolYearID, gibbonFinanceInvoiceeID, invoiceTo, billingScheduleType, status, invoiceIssueDate, invoiceDueDate, paidDate, paidAmount, notes, `key`, gibbonPersonIDCreator) VALUES ($year, $invoicee, 'Company', 'Ad Hoc', 'Paid - Partial', CURDATE(), CURDATE(), CURDATE(), 5, '', 'receipt-test', 1)");
    $id = $pdo->lastInsertId();
    $pdo->exec("INSERT INTO gibbonFinanceInvoiceFee (gibbonFinanceInvoiceID, feeType, name, description, gibbonFinanceFeeCategoryID, fee, sequenceNumber) VALUES ($id, 'Ad Hoc', 'Receipt test', '', $category, 8, 0)");
    $invoices[$who] = [$id, $personID];
}

$payment = function ($invoiceID, $personID, $amount, $txn, $offset) use ($pdo) {
    $st = $pdo->prepare("INSERT INTO gibbonPayment (foreignTable, foreignTableID, gibbonPersonID, type, status, amount, gateway, onlineTransactionStatus, paymentTransactionID, timestamp) VALUES ('gibbonFinanceInvoice', ?, ?, 'Online', 'Complete', ?, 'PayPal', 'Success', ?, NOW() + INTERVAL ? MINUTE)");
    $st->execute([$invoiceID, $personID, $amount, $txn, $offset]);
};

$check = function ($label, $invoiceID, $expectTxn, $expectNumber) use ($pdo, $guid, $year) {
    $ok = true;
    foreach (['old' => 'JOIN', 'new' => 'LEFT JOIN'] as $mode => $join) {
        // The count from invoices_payOnlineProcess.php line 254, then the number passed on line 260
        $st = $pdo->prepare("SELECT gibbonPayment.* FROM gibbonPayment $join gibbonPerson ON (gibbonPayment.gibbonPersonID=gibbonPerson.gibbonPersonID) WHERE foreignTable='gibbonFinanceInvoice' AND foreignTableID=? ORDER BY timestamp, gibbonPaymentID");
        $st->execute([$invoiceID]);
        $count = $st->rowCount();
        $number = $mode == 'old' ? $count : $count - 1;

        $text = strip_tags(str_replace(['<br/>', '</td>', '</div>', '</span>'], "\n", receiptContents($guid, $pdo, $invoiceID, $year, '', true, $number)));
        $shown = preg_match('/Receipt Number \(on this invoice\)\s*(\d+)/', $text, $m) ? $m[1] : '?';
        $noRecords = strpos($text, 'There are no records to display') !== false;
        $right = !$noRecords && $shown == $expectNumber && strpos($text, $expectTxn) !== false;
        if ($mode == 'new' && !$right) $ok = false;
        printf("%-4s %-36s receipt %s, %s\n", $mode, $label, $shown, $noRecords ? 'no payment details' : ($right ? 'correct' : 'wrong payment'));
    }
    return $ok;
};

$pass = true;
foreach ($invoices as $who => [$id, $personID]) {
    $payment($id, $personID, 5, "TEST-$id-1", 0);
    $pass = $check("$who, first payment", $id, "TEST-$id-1", 1) && $pass;
    $payment($id, $personID, 3, "TEST-$id-2", 1);
    $pass = $check("$who, second payment", $id, "TEST-$id-2", 2) && $pass;
}

$ids = implode(',', array_column($invoices, 0));
$pdo->exec("DELETE FROM gibbonPayment WHERE foreignTable='gibbonFinanceInvoice' AND foreignTableID IN ($ids)");
$pdo->exec("DELETE FROM gibbonFinanceInvoiceFee WHERE gibbonFinanceInvoiceID IN ($ids)");
$pdo->exec("DELETE FROM gibbonFinanceInvoice WHERE gibbonFinanceInvoiceID IN ($ids)");
$pdo->exec("DELETE FROM gibbonFinanceInvoicee WHERE gibbonFinanceInvoiceeID=$invoicee");

echo $pass ? "PASS: the fixed receipt number is right in every case.\n" : "FAIL\n";
