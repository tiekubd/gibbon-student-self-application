# Student Self-Application: Phase 2 (Gibbon v30.0.01)

Links a student's admissions account to the student, so they can return to it, without
ever recording a student as their own parent. Four complete replacement files, paths
relative to the Gibbon root. Requires Phase 1.1 already installed. No database changes.

## Files

| File | Change |
|---|---|
| `modules/Admissions/applications_manage_acceptProcess.php` | On a form without parent fields, link the account to the new student after acceptance (if the account is not linked yet and the student has no other account). Do not treat the account's person as Parent 1 when the form has no parent fields and that person is a Student. |
| `modules/Admissions/applications_manage_edit.php` | Same guard for the "attached to an admissions account for {name}" parent notice. |
| `src/Forms/Builder/FormPrefill.php` | New `setAccountEmail()`; on forms without parent fields, pre-fills Student Contact > Email with the account email (editable). |
| `modules/Admissions/applicationForm.php` | One line: passes the account email to `FormPrefill`. |

**The guard.** The account's person is skipped as Parent 1 only when BOTH: the form has no
parent fields (`parent1surname`, `parent1preferredName`, `parent1email`) AND that person's
primary role category is Student. Accounts linked to parents behave exactly as in v30.
An accepted student who applies on a parent form (e.g. for their own child) is Parent 1.

## Install

Back up, upload, verify checksums (from the webroot):

| File | Before (stock v30.0.01) | After |
|---|---|---|
| applicationForm.php | `2cb8e503612ab106e2628d847a6fdd28` | `ca04a564d3c97334c19378351f8e3279` |
| applications_manage_acceptProcess.php | `94a60123ecc76725d55017164035cd8b` | `d1842ecace27d290b8a1e62634de802b` |
| applications_manage_edit.php | `f5634305bdde1aec3819eb8f6ca64291` | `53cb3e8c70331a37cef73b15496a84e6` |
| FormPrefill.php | `bd798ce3cc756b33169dd3ab0a4b26e3` | `6bfd3ba737de62b19ab0f7fcd6f78805` |

Rollback: restore the `.v30bak` copies.

## Tested

On a local install of the official v30.0.01 release bundle (PHP 8.3, MariaDB) with
Phase 1.1 installed, driving the real pages over HTTP: 14 / 14 scenario checks pass.
Original v30 files: 10 / 14 (no pre-fill, account never linked, adult-student-as-parent
not recognised). Linking without the guard: the student becomes their own Parent 1 on a
second application, which the guard prevents. Parent-form regression checks pass on all
versions. No PHP warnings or errors from Gibbon code during the runs.

## Known limitation (unchanged from v30)

Accepting a second application from the same student creates a second student record,
just as a parent's second application for an already-enrolled child would. Merging or
re-using the existing student on acceptance is a separate, larger change.
