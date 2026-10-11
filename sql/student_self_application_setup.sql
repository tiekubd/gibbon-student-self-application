-- =====================================================================
-- Student Self-Application: test form setup (Phase 0)
-- Source:  'Sample Application Form' (copied from YOUR database, so any
--          edits you've made to the sample carry over)
-- Target:  'Student Self-Application'
--
-- Run ONE STEP AT A TIME and check the result before moving on.
-- Every step re-derives the form IDs by name, so it works in phpMyAdmin,
-- where each run can use a new connection and @variables are lost.
-- Nothing here changes the Sample Application Form itself.
-- =====================================================================


-- ---------------------------------------------------------------------
-- STEP 0: Pre-check (read only)
-- Expect: exactly 1 source row; 0 target rows; 5 pages on the source.
-- ---------------------------------------------------------------------
SELECT gibbonFormID, name, type, active, public FROM gibbonForm
WHERE name IN ('Sample Application Form', 'Student Self-Application');

SELECT p.gibbonFormPageID, p.name, p.sequenceNumber, COUNT(f.gibbonFormFieldID) AS fields
FROM gibbonFormPage p
LEFT JOIN gibbonFormField f ON f.gibbonFormPageID = p.gibbonFormPageID
WHERE p.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Sample Application Form')
GROUP BY p.gibbonFormPageID ORDER BY p.sequenceNumber;


-- ---------------------------------------------------------------------
-- STEP 1: Create the form record with the adjusted config
--   createParents                 -> N
--   createFamily                  -> Y   (Run A; Step 5 switches it for Run B)
--   acceptanceEmailStudentDefault -> Y
--   acceptanceEmailParent*        -> removed (no parent to email)
--   active / public               -> Y / Y
-- Everything else stays as in the sample.
-- ---------------------------------------------------------------------
INSERT INTO gibbonForm (name, description, type, active, public, gibbonYearGroupIDList, config)
SELECT 'Student Self-Application',
       'Phase 0 test: application completed by the student, no parent/guardian sections.',
       type, 'Y', 'Y', gibbonYearGroupIDList,
       JSON_REMOVE(
           JSON_SET(config,
               '$.createParents', 'N',
               '$.createFamily', 'Y',
               '$.acceptanceEmailStudentDefault', 'Y'),
           '$.acceptanceEmailParentDefault',
           '$.acceptanceEmailParentTemplate')
FROM gibbonForm
WHERE name = 'Sample Application Form';

-- Verify STEP 1: expect 1 row, createParents=N, createFamily=Y, parent keys NULL
SELECT gibbonFormID, name, active, public,
       JSON_UNQUOTE(JSON_EXTRACT(config, '$.createParents'))                 AS createParents,
       JSON_UNQUOTE(JSON_EXTRACT(config, '$.createFamily'))                  AS createFamily,
       JSON_UNQUOTE(JSON_EXTRACT(config, '$.acceptanceEmailStudentDefault')) AS emailStudent,
       JSON_EXTRACT(config, '$.acceptanceEmailParentTemplate')               AS parentTemplate,
       JSON_EXTRACT(config, '$.enableLimitedYearsOfEntry')                   AS limitedYears,
       JSON_EXTRACT(config, '$.availableYearsOfEntry')                       AS yearsOfEntry
FROM gibbonForm WHERE name = 'Student Self-Application';
-- NOTE: if limitedYears = "Y", check that yearsOfEntry are real
-- gibbonSchoolYearIDs in your test DB, or the Year of Entry list will be empty.


-- ---------------------------------------------------------------------
-- STEP 2: Copy every page except 'Family'
-- ---------------------------------------------------------------------
INSERT INTO gibbonFormPage (gibbonFormID, name, introduction, postscript, sequenceNumber)
SELECT (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Student Self-Application'),
       p.name, p.introduction, p.postscript, p.sequenceNumber
FROM gibbonFormPage p
WHERE p.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Sample Application Form')
  AND p.name <> 'Family'
ORDER BY p.sequenceNumber;

-- Verify STEP 2: expect 4 pages: Student, Enrolment, Documents, Final Details
SELECT gibbonFormPageID, name, sequenceNumber FROM gibbonFormPage
WHERE gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Student Self-Application')
ORDER BY sequenceNumber;


-- ---------------------------------------------------------------------
-- STEP 3: Copy the fields for those pages (matched by page name),
--         and make the student's email required (it is now the contact).
-- ---------------------------------------------------------------------
INSERT INTO gibbonFormField (gibbonFormPageID, fieldName, fieldType, fieldGroup, required, hidden,
                             prefill, options, label, description, conditional, defaultValue, sequenceNumber)
SELECT np.gibbonFormPageID, f.fieldName, f.fieldType, f.fieldGroup,
       CASE WHEN f.fieldName = 'email' THEN 'Y' ELSE f.required END,
       f.hidden, f.prefill, f.options, f.label, f.description, f.conditional, f.defaultValue, f.sequenceNumber
FROM gibbonFormField f
JOIN gibbonFormPage op ON op.gibbonFormPageID = f.gibbonFormPageID
JOIN gibbonFormPage np ON np.name = op.name
     AND np.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Student Self-Application')
WHERE op.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Sample Application Form')
  AND op.name <> 'Family';

-- Verify STEP 3: field counts per page should match STEP 0 (minus Family)
SELECT p.name, COUNT(f.gibbonFormFieldID) AS fields,
       SUM(f.fieldName = 'email' AND f.required = 'Y') AS emailRequired
FROM gibbonFormPage p
LEFT JOIN gibbonFormField f ON f.gibbonFormPageID = p.gibbonFormPageID
WHERE p.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Student Self-Application')
GROUP BY p.gibbonFormPageID ORDER BY p.sequenceNumber;

-- And confirm no parent fields came across: expect 0 rows
SELECT f.fieldName, f.fieldGroup FROM gibbonFormField f
JOIN gibbonFormPage p ON p.gibbonFormPageID = f.gibbonFormPageID
WHERE p.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Student Self-Application')
  AND (f.fieldGroup IN ('Parent1Fields', 'Parent2Fields') OR f.fieldName LIKE 'parent%');


-- ---------------------------------------------------------------------
-- STEP 4: Bring the home address fields over from the old Family page,
--         appended to the end of the Student page.
--         (CreateFamily requires 'homeAddress'; it also gives the student
--          an address to live on.)
-- ---------------------------------------------------------------------
INSERT INTO gibbonFormField (gibbonFormPageID, fieldName, fieldType, fieldGroup, required, hidden,
                             prefill, options, label, description, conditional, defaultValue, sequenceNumber)
SELECT (SELECT np.gibbonFormPageID FROM gibbonFormPage np
         WHERE np.name = 'Student'
           AND np.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Student Self-Application')),
       f.fieldName, f.fieldType, f.fieldGroup, f.required, f.hidden, f.prefill, f.options,
       f.label, f.description, f.conditional, f.defaultValue,
       1000 + f.sequenceNumber
FROM gibbonFormField f
JOIN gibbonFormPage op ON op.gibbonFormPageID = f.gibbonFormPageID
WHERE op.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Sample Application Form')
  AND op.name = 'Family'
  AND f.fieldName IN ('headingHomeAddress', 'homeAddress', 'homeAddressDistrict', 'homeAddressCountry');

-- Verify STEP 4: expect 4 rows at the end of the Student page
SELECT f.fieldName, f.fieldGroup, f.required, f.sequenceNumber
FROM gibbonFormField f
JOIN gibbonFormPage p ON p.gibbonFormPageID = f.gibbonFormPageID
WHERE p.name = 'Student'
  AND p.gibbonFormID = (SELECT gibbonFormID FROM gibbonForm WHERE name = 'Student Self-Application')
ORDER BY f.sequenceNumber DESC LIMIT 5;

-- Now open System Admin > Form Builder > Student Self-Application.
-- The page lists any missing required fields per process. Screenshot it.
-- Then submit Run A.


-- ---------------------------------------------------------------------
-- STEP 5 (after Run A only): switch to Run B, with no family created
-- ---------------------------------------------------------------------
UPDATE gibbonForm
SET config = JSON_SET(config, '$.createFamily', 'N')
WHERE name = 'Student Self-Application';

SELECT name, JSON_UNQUOTE(JSON_EXTRACT(config, '$.createFamily')) AS createFamily
FROM gibbonForm WHERE name = 'Student Self-Application';


-- ---------------------------------------------------------------------
-- ROLLBACK: remove the test form completely (fields -> pages -> form)
-- Only delete applications made with it if you want them gone as well.
-- ---------------------------------------------------------------------
-- DELETE f FROM gibbonFormField f
--   JOIN gibbonFormPage p ON p.gibbonFormPageID = f.gibbonFormPageID
--   WHERE p.gibbonFormID = (SELECT id FROM (SELECT gibbonFormID AS id FROM gibbonForm WHERE name = 'Student Self-Application') x);
-- DELETE FROM gibbonFormPage
--   WHERE gibbonFormID = (SELECT id FROM (SELECT gibbonFormID AS id FROM gibbonForm WHERE name = 'Student Self-Application') x);
-- DELETE FROM gibbonForm WHERE name = 'Student Self-Application';
