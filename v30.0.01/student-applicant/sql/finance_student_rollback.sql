-- =====================================================================
-- Undo finance_student.sql: removes 'Student' from invoiceTo
-- Run AFTER `bash student-applicant.sh rollback` has restored the files.
-- Anything billed to Student is switched to Family first, so no row is lost.
-- Run ONE STEP AT A TIME and check its result. Back up the database first.
-- =====================================================================


-- ---------------------------------------------------------------------
-- STEP 0: What will be switched (read only)
-- ---------------------------------------------------------------------
SELECT 'gibbonFinanceInvoicee' AS tableName, COUNT(*) AS studentRows FROM gibbonFinanceInvoicee WHERE invoiceTo = 'Student'
UNION ALL SELECT 'gibbonFinanceInvoice', COUNT(*) FROM gibbonFinanceInvoice WHERE invoiceTo = 'Student'
UNION ALL SELECT 'gibbonFinanceInvoiceeUpdate', COUNT(*) FROM gibbonFinanceInvoiceeUpdate WHERE invoiceTo = 'Student';


-- ---------------------------------------------------------------------
-- STEP 1: Switch Student to Family
-- ---------------------------------------------------------------------
UPDATE gibbonFinanceInvoicee SET invoiceTo = 'Family' WHERE invoiceTo = 'Student';
UPDATE gibbonFinanceInvoice SET invoiceTo = 'Family' WHERE invoiceTo = 'Student';
UPDATE gibbonFinanceInvoiceeUpdate SET invoiceTo = 'Family' WHERE invoiceTo = 'Student';


-- ---------------------------------------------------------------------
-- STEP 2: Restore the stock column definitions
-- ---------------------------------------------------------------------
ALTER TABLE gibbonFinanceInvoicee
  MODIFY invoiceTo enum('Family','Company') NOT NULL;

ALTER TABLE gibbonFinanceInvoice
  MODIFY invoiceTo enum('Family','Company') NOT NULL DEFAULT 'Family';

ALTER TABLE gibbonFinanceInvoiceeUpdate
  MODIFY invoiceTo enum('Family','Company') NOT NULL;


-- ---------------------------------------------------------------------
-- STEP 3: Check (read only)
-- Expect: 3 rows, each enum('Family','Company').
-- ---------------------------------------------------------------------
SELECT TABLE_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND COLUMN_NAME = 'invoiceTo'
  AND TABLE_NAME IN ('gibbonFinanceInvoicee', 'gibbonFinanceInvoice', 'gibbonFinanceInvoiceeUpdate')
ORDER BY TABLE_NAME;
