# Upstream bug reports

Four v30.0.01 bugs found while testing student applications, filed as GitHub issues. Each one affects any
school, and each was still present in the development branch on 9 October 2026 (commit `1d83c2b`).
A third, an acceptance email issue, was reported privately to the Gibbon team, following Gibbon's
security policy. Line
numbers are from that commit. Each fix is in `v30.0.01/student-applicant` and adds no new strings.

---

## 1. Family page fails for an admissions account that has a family but no person

Filed as [#2183](https://github.com/GibbonEdu/core/issues/2183).

**Where:** `src/Forms/Builder/Fields/FamilyFields.php`, `addFieldToForm()` (lines 121 to 140) and
`shouldValidate()` (line 231).

**How an account gets into this state:** a form without Parent 1 is accepted with Create Family
on. Gibbon links the admissions account to the new family but not to any person.

**Steps (stock v30.0.01):**
1. Use a copy of the Sample form with the Parent 1 and Parent 2 fields removed, the home address fields kept, and Create Family on.
2. Submit and accept an application. The admissions account now has `gibbonFamilyID` set and `gibbonPersonID` NULL.
3. Submit a second application with the same email.
4. As staff, open the second application in Manage Applications > Edit. Staff Add for that account fails the same way.

**Actual:** a fatal error and no form:

```
Warning: Undefined variable $families in .../FamilyFields.php on line 140
Uncaught Exception: TypeError - current(): Argument #1 ($array) must be of type array, null given
```

**Cause:**
- `$families` is only assigned inside `if ($formBuilder->hasConfig('gibbonPersonID'))`, but line 127 enters the family branch when only `gibbonFamilyID` is set.
- `shouldValidate()` skips validation of the hidden address fields only when `gibbonPersonID` is set. So once the crash is fixed, the page hides the address fields but still requires them, and it cannot be submitted.

**Fix:**
- Initialise `$families = [];`. When there is no person but there is a family, offer that family (`getByID`), and branch on `!empty($families)`.
- In `shouldValidate()`, use the same test as the display:

```php
        if ($formBuilder->hasConfig('gibbonPersonID') || $formBuilder->hasConfig('gibbonFamilyID')) return false;
```

---

## 2. "Submission Email" line missing after submitting a form without a Parent 1 email

Filed as [#2184](https://github.com/GibbonEdu/core/issues/2184).

**Where:** `src/Forms/Builder/View/SendSubmissionEmailView.php`, `display()` (line 72).

**Steps:** submit an application on a form that has Send Submission Email on and no `parent1email`
field (for example, a form for adult students).

**Expected:** the results page lists "Submission Email: An email was sent to …".

**Actual:** the line is missing, although the email was sent. Staff viewing the application do see
it.

**Cause:** `SendSubmissionEmail` records the address as a result:
`setResult('submissionEmail', ...)` (`Process/SendSubmissionEmail.php`, line 133). The view checks
`$data->has('submissionEmail')`. Outside read-only mode, `has()` only looks at form data, not
results, so on the applicant's page the check fails unless `parent1email` is present.

**Fix:**

```php
        if (!$data->hasResult('submissionEmail') && !$data->has('submissionEmail') && !$data->has('parent1email')) return;
```

---

## 3. Online invoice payment receipt is incomplete when the payer is logged in

Filed as [#2201](https://github.com/GibbonEdu/core/issues/2201).

**Where:** `modules/Finance/invoices_payOnlineProcess.php`, lines 254 and 260.

**Steps:**
1. Admin > School Admin > Finance Settings: set Enable Online Payment to Yes, with a payment gateway configured (tested with the PayPal sandbox).
2. Finance > Manage Invoices: issue an invoice and email it to the invoicee.
3. In a browser where you are logged in to Gibbon, open the Pay Now link from the invoice email and pay.
4. Open the receipt email. For comparison, pay a second invoice from a private window, not logged in.

**Expected:** Status "Paid (Complete)", "Receipt Number (on this invoice): 1", and a Payment Details table listing the payment.

**Actual:** Status is blank, the receipt number is 2, and Payment Details says "There are no records to display". The payment is recorded correctly and the invoice is marked Paid. Paying while not logged in gives a correct receipt.

**Cause:**
- Line 260 passes `$receiptCount` to `receiptContents()`, which expects a zero-based receipt number (`LIMIT $receiptNumber, 1`, displayed as `$receiptNumber + 1`). The staff path, `invoices_manage_editProcess.php` line 253, passes `$receiptCount-1`.
- Line 254 counts payments with an inner `JOIN gibbonPerson`. A payer who isn't logged in is saved with `gibbonPersonID` NULL and isn't counted, so the count is 0: right by chance for a first payment, but every later payment by such a payer gets receipt 1, the first payment, again.

**Fix:**

```php
                $sqlPayments = 'SELECT gibbonPayment.*, surname, preferredName FROM gibbonPayment LEFT JOIN gibbonPerson ON (gibbonPayment.gibbonPersonID=gibbonPerson.gibbonPersonID) WHERE foreignTable=:foreignTable AND foreignTableID=:foreignTableID ORDER BY timestamp, gibbonPaymentID';
```

and pass `$receiptCount-1` to `receiptContents()`. Optionally, `moduleFunctions.php` line 1122 (`LIMIT $receiptNumber, 1`) has no `ORDER BY`; adding `ORDER BY timestamp, gibbonPaymentID` would match the count.

Checked with `tests/finance-receipt/receipt_test.php`: with the fix, first and second payments by payers logged in and not all get the right receipt.

---

## 4. Online payment receipt for a Company invoice goes to the family

Filed as [#2202](https://github.com/GibbonEdu/core/issues/2202). Confirmed on a live v30.0.01 site with the PayPal sandbox: the same Company invoicee's receipt was delivered to the father on stock, and to the company email with the fix.

**Where:** `modules/Finance/invoices_payOnlineProcess.php`, line 156.

**Steps:** set a student's invoicee to Company with a company email, and the family's adults with their own emails. Issue an invoice and pay it online.

**Expected:** the receipt goes to the company email (and the family only if "CC Family?" is Yes).

**Actual:** the receipt goes to the family.

**Cause:** the check that the invoice was found assigns instead of comparing:

```php
    if ($gibbonFinanceInvoiceID == '' or $key == '' or $gibbonFinanceInvoiceeID == '' or $invoiceTo = '' or $gibbonSchoolYearID == '') {
```

`$invoiceTo = ''` sets `$invoiceTo` to an empty string (and is false, so the check still passes). The receipt code then tests `$invoiceTo == 'Company'`, which is never true, and sends to the family.

**Fix:** `$invoiceTo == ''`.

---

Already fixed upstream, so not reported: Auto House Assign wrote each new student's house to person 1
(`$formData->has('gibbonPersonIDStudent')` passed as the ID). Fixed in
[PR #2121](https://github.com/GibbonEdu/core/pull/2121). A v30.0.01 hotfix and repair script are in
`v30.0.01/hotfix-assignhouse`.
