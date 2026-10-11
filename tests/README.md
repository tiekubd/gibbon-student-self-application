# Tests

Both suites were used to verify the changes in this repository. **Never run them against a
real school's Gibbon:** the end-to-end scenarios create admissions accounts, applications,
students, parents and families.

## `phase1-harness/harness.php`

Runs the changed form-builder processes against Gibbon v30.0.01's own classes, with the
mailer, session, payment gateway and email template stubbed out. No database or web server.

```bash
export GIBBON_ROOT=/path/to/gibbon-v30.0.01   # unpacked source
mkdir -p orig new                              # stock and changed copies of the Phase 1 files,
                                               # in Gibbon's src/ and modules/ layout
php harness.php new    # expect 20 / 20
php harness.php orig   # stock v30.0.01: reproduces "Dear ,", the boolean recipient, etc.
```

## `end-to-end/scenarios.py`

Drives a throwaway local Gibbon v30.0.01 over HTTP like a browser: applies, accepts as an
admin, applies again, and checks the results in the database. Scenarios: a new student; the
same student applying again; a parent applying; the same parent applying for a sibling; an
accepted student applying for their own child on a parent form.

Needs: Python 3, the `mysql` client with access to the test database, a fresh v30.0.01
install with Phases 1 and 2 copied in, `publicApplications` on, and the Student
Self-Application form created with `sql/student_self_application_setup.sql`. The form IDs
in the script assume the Sample Application Form is `000001` and the test form `000002`.

```bash
export GIBBON_URL=http://127.0.0.1:8088 GIBBON_DB=gibbon_test \
       GIBBON_ADMIN_USER=admin GIBBON_ADMIN_PASS='...'
python3 scenarios.py run1   # the argument tags this run's test email addresses
```

Expected: 14 / 14 with Phase 2; 10 / 14 on stock v30.0.01.
