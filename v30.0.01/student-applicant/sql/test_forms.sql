-- =====================================================================
-- Applicant type: test forms for a FRESH Gibbon v30.0.01 test site
--
-- Creates three forms, all copied from the Sample Application Form:
--   Student Self-Application              "The student, for themselves"; no parent or Family pages
--   Application by a student              "The student, for themselves"; parent sections kept
--   Application by a parent or guardian   "A parent or guardian, for a student", saved explicitly
-- The last two are the pair a school accepting both kinds of applicant would publish.
-- The Sample Application Form stays a parent form (no setting = parent).
--
-- Run ONE STEP AT A TIME and check its result before moving on. Every step
-- finds forms by name, so it works in phpMyAdmin (no @variables).
-- Test sites only.
-- =====================================================================


-- ---------------------------------------------------------------------
-- STEP 0: Pre-check (read only)
-- Expect: 1 row, the Sample Application Form, and no test forms yet.
-- ---------------------------------------------------------------------
SELECT gibbonFormID, name, active, public,
       JSON_UNQUOTE(JSON_EXTRACT(config, '$.applicantType')) AS applicantType
FROM gibbonForm ORDER BY gibbonFormID;


-- ---------------------------------------------------------------------
-- STEP 1: Make the Sample Application Form active and public
-- (same as Form Builder > Edit > Active / Public = Yes). The demo data
-- installs it inactive. Its applicant setting is left unset = parent.
-- ---------------------------------------------------------------------
UPDATE gibbonForm SET active = 'Y', public = 'Y' WHERE name = 'Sample Application Form';

-- Verify STEP 1: active Y, public Y
SELECT gibbonFormID, name, active, public FROM gibbonForm WHERE name = 'Sample Application Form';


-- ---------------------------------------------------------------------
-- STEP 2: Create the three forms (settings only; pages and fields follow)
-- ---------------------------------------------------------------------
INSERT INTO gibbonForm (name, description, type, active, public, gibbonYearGroupIDList, config)
SELECT 'Student Self-Application', 'The student applies for themselves; no parent sections.',
       type, 'Y', 'Y', gibbonYearGroupIDList,
       JSON_REMOVE(
           JSON_SET(config, '$.applicantType', 'Student', '$.createParents', 'N', '$.createFamily', 'Y',
                    '$.acceptanceEmailStudentDefault', 'Y'),
           '$.acceptanceEmailParentDefault', '$.acceptanceEmailParentTemplate')
FROM gibbonForm WHERE name = 'Sample Application Form';

INSERT INTO gibbonForm (name, description, type, active, public, gibbonYearGroupIDList, config)
SELECT 'Application by a student', 'For students applying for themselves. Parent or guardian details are still collected.',
       type, 'Y', 'Y', gibbonYearGroupIDList,
       JSON_SET(config, '$.applicantType', 'Student', '$.createParents', 'Y', '$.createFamily', 'Y',
                '$.enableLimitedYearsOfEntry', 'N', '$.acceptanceEmailStudentDefault', 'Y')
FROM gibbonForm WHERE name = 'Sample Application Form';

INSERT INTO gibbonForm (name, description, type, active, public, gibbonYearGroupIDList, config)
SELECT 'Application by a parent or guardian', 'For parents or guardians applying for a student.',
       type, 'Y', 'Y', gibbonYearGroupIDList,
       JSON_SET(config, '$.applicantType', 'Parent', '$.createParents', 'Y', '$.createFamily', 'Y',
                '$.enableLimitedYearsOfEntry', 'N')
FROM gibbonForm WHERE name = 'Sample Application Form';

-- Verify STEP 2: 4 rows. Sample NULL (= parent); Student, Student, Parent.
-- On a fresh site the IDs are 000001 to 000004.
SELECT gibbonFormID, name, active, public,
       JSON_UNQUOTE(JSON_EXTRACT(config, '$.applicantType')) AS applicantType,
       JSON_UNQUOTE(JSON_EXTRACT(config, '$.createParents')) AS createParents
FROM gibbonForm ORDER BY gibbonFormID;


-- ---------------------------------------------------------------------
-- STEP 3: Copy the pages. Student Self-Application gets every page except Family.
-- ---------------------------------------------------------------------
INSERT INTO gibbonFormPage (gibbonFormID, name, introduction, postscript, sequenceNumber)
SELECT n.gibbonFormID, p.name, p.introduction, p.postscript, p.sequenceNumber
FROM gibbonFormPage p
JOIN gibbonForm s ON s.gibbonFormID = p.gibbonFormID AND s.name = 'Sample Application Form'
JOIN gibbonForm n ON n.name IN ('Student Self-Application', 'Application by a student', 'Application by a parent or guardian')
WHERE NOT (n.name = 'Student Self-Application' AND p.name = 'Family');

-- Verify STEP 3: Student Self-Application 4 pages; the other two 5 pages each
SELECT f.name, COUNT(*) AS pages FROM gibbonFormPage p
JOIN gibbonForm f ON f.gibbonFormID = p.gibbonFormID GROUP BY f.gibbonFormID ORDER BY f.gibbonFormID;


-- ---------------------------------------------------------------------
-- STEP 4: Copy the fields, matched by page name. On Student Self-Application
-- the student's email is made required, since it is the contact address.
-- ---------------------------------------------------------------------
INSERT INTO gibbonFormField (gibbonFormPageID, fieldName, fieldType, fieldGroup, required, hidden,
                             prefill, options, label, description, conditional, defaultValue, sequenceNumber)
SELECT np.gibbonFormPageID, f.fieldName, f.fieldType, f.fieldGroup,
       CASE WHEN n.name = 'Student Self-Application' AND f.fieldName = 'email' THEN 'Y' ELSE f.required END,
       f.hidden, f.prefill, f.options, f.label, f.description, f.conditional, f.defaultValue, f.sequenceNumber
FROM gibbonFormField f
JOIN gibbonFormPage op ON op.gibbonFormPageID = f.gibbonFormPageID
JOIN gibbonForm s ON s.gibbonFormID = op.gibbonFormID AND s.name = 'Sample Application Form'
JOIN gibbonForm n ON n.name IN ('Student Self-Application', 'Application by a student', 'Application by a parent or guardian')
JOIN gibbonFormPage np ON np.gibbonFormID = n.gibbonFormID AND np.name = op.name;

-- Verify STEP 4: the two 'Application by' forms have the same count as the Sample;
-- Student Self-Application has fewer (no Family page)
SELECT fo.name, COUNT(f.gibbonFormFieldID) AS fields FROM gibbonForm fo
JOIN gibbonFormPage p ON p.gibbonFormID = fo.gibbonFormID
LEFT JOIN gibbonFormField f ON f.gibbonFormPageID = p.gibbonFormPageID
GROUP BY fo.gibbonFormID ORDER BY fo.gibbonFormID;


-- ---------------------------------------------------------------------
-- STEP 5: Student Self-Application: bring the home address fields over from
-- the Sample's Family page, at the end of the Student page (Create Family
-- needs homeAddress).
-- ---------------------------------------------------------------------
INSERT INTO gibbonFormField (gibbonFormPageID, fieldName, fieldType, fieldGroup, required, hidden,
                             prefill, options, label, description, conditional, defaultValue, sequenceNumber)
SELECT np.gibbonFormPageID, f.fieldName, f.fieldType, f.fieldGroup, f.required, f.hidden, f.prefill,
       f.options, f.label, f.description, f.conditional, f.defaultValue, 1000 + f.sequenceNumber
FROM gibbonFormField f
JOIN gibbonFormPage op ON op.gibbonFormPageID = f.gibbonFormPageID AND op.name = 'Family'
JOIN gibbonForm s ON s.gibbonFormID = op.gibbonFormID AND s.name = 'Sample Application Form'
JOIN gibbonForm n ON n.name = 'Student Self-Application'
JOIN gibbonFormPage np ON np.gibbonFormID = n.gibbonFormID AND np.name = 'Student'
WHERE f.fieldName IN ('headingHomeAddress', 'homeAddress', 'homeAddressDistrict', 'homeAddressCountry');

-- Verify STEP 5: 4 rows; and no parent fields on Student Self-Application (second query: 0)
SELECT f.fieldName, f.sequenceNumber FROM gibbonFormField f
JOIN gibbonFormPage p ON p.gibbonFormPageID = f.gibbonFormPageID AND p.name = 'Student'
JOIN gibbonForm fo ON fo.gibbonFormID = p.gibbonFormID AND fo.name = 'Student Self-Application'
WHERE f.sequenceNumber > 1000;

SELECT COUNT(*) AS parentFields FROM gibbonFormField f
JOIN gibbonFormPage p ON p.gibbonFormPageID = f.gibbonFormPageID
JOIN gibbonForm fo ON fo.gibbonFormID = p.gibbonFormID AND fo.name = 'Student Self-Application'
WHERE f.fieldName LIKE 'parent%' OR f.fieldGroup IN ('Parent1Fields', 'Parent2Fields');


-- ---------------------------------------------------------------------
-- ROLLBACK: remove the three test forms (fields, pages, forms). Applications
-- made with them are not deleted.
-- ---------------------------------------------------------------------
-- DELETE f FROM gibbonFormField f JOIN gibbonFormPage p ON p.gibbonFormPageID = f.gibbonFormPageID
--   JOIN gibbonForm fo ON fo.gibbonFormID = p.gibbonFormID
--   WHERE fo.name IN ('Student Self-Application', 'Application by a student', 'Application by a parent or guardian');
-- DELETE p FROM gibbonFormPage p JOIN gibbonForm fo ON fo.gibbonFormID = p.gibbonFormID
--   WHERE fo.name IN ('Student Self-Application', 'Application by a student', 'Application by a parent or guardian');
-- DELETE FROM gibbonForm WHERE name IN ('Student Self-Application', 'Application by a student', 'Application by a parent or guardian');
