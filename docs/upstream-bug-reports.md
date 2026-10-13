# Draft upstream bug reports

Three v30.0.01 bugs found while testing student applications. Each one affects any school, and
each was still present in the development branch on 9 October 2026 (commit `1d83c2b`). Line
numbers are from that commit. Each fix is in `v30.0.01/student-applicant` and adds no new strings.

---

## 1. Acceptance welcome emails are also sent to everyone emailed before them

**Where:** `src/Forms/Builder/Process/SendAcceptanceEmail.php`, `sendWelcomeEmail()` (line 94).

**Steps:**
1. Use a form with parent fields and acceptance emails set up (both templates chosen).
2. Submit an application with a student email, Parent 1 and Parent 2, each with a different address.
3. Accept it with both "Automatically inform student" and "Automatically inform parents" ticked.

**Expected:** three welcome emails, each to one person, with that person's own username and password.

**Actual:**
- The student's email goes to the student.
- Parent 1's email, with Parent 1's password, goes to the student and Parent 1.
- Parent 2's email goes to the student, Parent 1 and Parent 2.

**Cause:** `process()` calls `sendWelcomeEmail()` up to three times with the same mailer. Each call
adds its recipients (lines 120 to 122), but the recipients from the previous call are never cleared.

**Fix:** clear the recipients at the start of each email, as `NotificationSender` already does:

```php
        // Setup the email
        $this->mail->clearAllRecipients();
        $this->mail->SetFrom(...);
```

---

## 2. Family page fails for an admissions account that has a family but no person

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

## 3. "Submission Email" line missing after submitting a form without a Parent 1 email

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

Already fixed upstream, so not reported: Auto House Assign wrote each new student's house to person 1
(`$formData->has('gibbonPersonIDStudent')` passed as the ID). Fixed in
[PR #2121](https://github.com/GibbonEdu/core/pull/2121). A v30.0.01 hotfix and repair script are in
`v30.0.01/hotfix-assignhouse`.
