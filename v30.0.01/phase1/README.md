# Student Self-Application: Phase 1 (Gibbon v30.0.01)

Complete replacement files (6: Phase 1 plus the Phase 1.1 display fixes). Paths are relative to the Gibbon root, so the folders in
this zip line up with your installation. Built and tested against the v30.0.01 tag only.

## Files

| File | Fixes |
|---|---|
| `src/Forms/Builder/Process/SendSubmissionEmail.php` | #3 "Dear ," greeting falls back to the student; `AddAddress(true)` bug (was passing `has()` instead of `get()`); no duplicate when parent1email = account email |
| `src/Forms/Builder/Process/PayProcessingFee.php` | #1 Processing fee works on forms without parent fields: sent to parent1email, else student email, else account email; greeting falls back to the student |
| `src/Forms/Builder/View/SendAcceptanceEmailView.php` | #4 Parent Acceptance Template is no longer required |
| `src/Forms/Builder/Process/SendAcceptanceEmail.php` | Guard: never tries a parent welcome email when no parent template is set |
| `modules/Admissions/applications_manage_accept.php` | #4 "Inform parents" checkbox only shown when the form has a `parent1email` field |
| `src/Forms/Builder/View/PayProcessingFeeView.php` | 1.1: description reads "to the applicant" instead of "to the parent" |

No database changes. Parent application forms behave exactly as before. Existing email
templates keep working: the `parentTitle` / `parentPreferredName` / `parentSurname`
variables are kept and filled with the student's name when no parent was collected.

## Install

1. Back up the six originals, e.g. copy each to `<name>.php.v30bak`.
2. Upload the six files over the originals (same paths).
3. No cache to clear; PHP picks them up on the next request.

Rollback: restore the `.v30bak` copies.

## Test on the instance

1. **Form Builder > Student Self-Application > Edit.**
   - Inactive Features lists Application Processing Fee with only `Payment Gateway` while online
     payment is off (1.1; Phase 1 alone still showed `parent1email` there).
   - Under the acceptance email settings, Parent Acceptance Template has no asterisk.
     Clear it and click Submit: it should save.
2. **Submit a new application** as a student (fresh email).
   - Confirmation email greets the student by name, not "Dear ,".
3. **Accept it.** The "inform parents" checkbox should not appear.
4. **Regression:** submit one application on a parent form (e.g. a copy of the Sample
   Application Form). Greeting uses Parent 1, and Parent 1 receives the confirmation email
   (before this fix the second recipient was the boolean `true`, so it never arrived).

## Not in Phase 1

Linking the admissions account to the student (#5, #9) needs design first:
`applications_manage_acceptProcess.php` treats an account's `gibbonPersonID` as Parent 1 on
every later application from that account, so a student linked to their own account
would be recorded as their own parent on a second application.
