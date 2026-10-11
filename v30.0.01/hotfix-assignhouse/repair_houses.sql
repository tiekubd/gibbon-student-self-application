-- Repair houses lost to the v30.0.01 AssignHouse bug (house written to person 1, not the student).
-- Run STEP 1, check it, then STEP 2. Only touches accepted students who have NO house
-- and whose application result recorded the house that was assigned.

-- STEP 1 (preview): students to repair, with the house the acceptance page reported
SELECT a.gibbonAdmissionsApplicationID, p.gibbonPersonID, p.username,
       p.gibbonHouseID AS currentHouse,
       JSON_UNQUOTE(JSON_EXTRACT(a.result, '$.gibbonHouseID')) AS assignedHouseID, h.name AS assignedHouse
FROM gibbonAdmissionsApplication a
JOIN gibbonPerson p ON p.gibbonPersonID = JSON_UNQUOTE(JSON_EXTRACT(a.result, '$.gibbonPersonIDStudent')) + 0
LEFT JOIN gibbonHouse h ON h.gibbonHouseID = JSON_UNQUOTE(JSON_EXTRACT(a.result, '$.gibbonHouseID'))
WHERE a.status = 'Accepted'
  AND JSON_EXTRACT(a.result, '$.gibbonHouseID') IS NOT NULL
  AND p.gibbonHouseID IS NULL;

-- STEP 2 (apply): give each of those students their assigned house
UPDATE gibbonPerson p
JOIN gibbonAdmissionsApplication a ON p.gibbonPersonID = JSON_UNQUOTE(JSON_EXTRACT(a.result, '$.gibbonPersonIDStudent')) + 0
SET p.gibbonHouseID = JSON_UNQUOTE(JSON_EXTRACT(a.result, '$.gibbonHouseID'))
WHERE a.status = 'Accepted'
  AND JSON_EXTRACT(a.result, '$.gibbonHouseID') IS NOT NULL
  AND p.gibbonHouseID IS NULL;
-- Then run STEP 1 again: expect 0 rows.
