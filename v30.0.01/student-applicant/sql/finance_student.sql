-- =====================================================================
-- Billing the student directly: adds "Student" to who an invoice is sent to
-- Gibbon v30.0.01. Run BEFORE uploading the Finance files.
--
-- Adds the value 'Student' to invoiceTo in three tables:
--   gibbonFinanceInvoicee         who each student's invoices go to
--   gibbonFinanceInvoice          who each invoice was billed to
--   gibbonFinanceInvoiceeUpdate   Data Updater change requests
-- Family and Company are unchanged; no existing row changes.
-- Undo with finance_student_rollback.sql (after restoring the files).
--
-- Run ONE STEP AT A TIME and check its result. Back up the database first.
-- =====================================================================


-- ---------------------------------------------------------------------
-- STEP 0: Pre-check (read only)
-- Expect: 3 rows, each enum('Family','Company').
-- ---------------------------------------------------------------------
SELECT TABLE_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND COLUMN_NAME = 'invoiceTo'
  AND TABLE_NAME IN ('gibbonFinanceInvoicee', 'gibbonFinanceInvoice', 'gibbonFinanceInvoiceeUpdate')
ORDER BY TABLE_NAME;


-- ---------------------------------------------------------------------
-- STEP 1: Add 'Student' (same NOT NULL and default as before)
-- ---------------------------------------------------------------------
ALTER TABLE gibbonFinanceInvoicee
  MODIFY invoiceTo enum('Family','Company','Student') NOT NULL;

ALTER TABLE gibbonFinanceInvoice
  MODIFY invoiceTo enum('Family','Company','Student') NOT NULL DEFAULT 'Family';

ALTER TABLE gibbonFinanceInvoiceeUpdate
  MODIFY invoiceTo enum('Family','Company','Student') NOT NULL;


-- ---------------------------------------------------------------------
-- STEP 2: Check (read only)
-- Expect: 3 rows, each enum('Family','Company','Student');
-- gibbonFinanceInvoice still defaults to 'Family'.
-- ---------------------------------------------------------------------
SELECT TABLE_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND COLUMN_NAME = 'invoiceTo'
  AND TABLE_NAME IN ('gibbonFinanceInvoicee', 'gibbonFinanceInvoice', 'gibbonFinanceInvoiceeUpdate')
ORDER BY TABLE_NAME;
