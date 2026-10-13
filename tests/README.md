# Tests

These scripts verified the package in `v30.0.01/student-applicant`. **Never run them against a
real school's Gibbon:** they create admissions accounts, applications, students, parents and
families, and `loggedin_test.py` expects a test student's password.

## `process-harness/harness.php`

Runs the changed email and fee processes against Gibbon v30.0.01's own classes, with the mailer,
session, payment gateway and email template stubbed out. No database or web server.

```bash
export GIBBON_ROOT=/path/to/gibbon-v30.0.01      # unpacked release source
php harness.php ../../v30.0.01/student-applicant  # expect 20 / 20
```

## `end-to-end/`

Drives a throwaway local Gibbon v30.0.01 over HTTP like a browser, then checks the database.

Needs:
- Python 3 and the `mysql` client with access to the test database;
- a fresh v30.0.01 install with the package installed and `publicApplications` on;
- the forms from `v30.0.01/student-applicant/sql/test_forms.sql` (Sample `000001`, Student Self-Application `000002`, Application by a student `000003`, Application by a parent or guardian `000004`);
- outgoing mail written to files, for example PHP's `sendmail_path` pointed at a script that saves each message to `$GIBBON_MAIL_DIR`.

```bash
export GIBBON_URL=http://127.0.0.1:8088 GIBBON_DB=gibbon_test \
       GIBBON_ADMIN_USER=admin GIBBON_ADMIN_PASS='...' GIBBON_MAIL_DIR=/path/to/mail
python3 applicant_scenarios.py run1   # 32 checks; the argument tags this run's test addresses
python3 scenarios.py run1             # 14 checks
python3 housetest.py run1             # the student gets the house, person 1 does not
GIBBON_STUDENT_PASS='...' python3 loggedin_test.py <accepted student username> 000003 run1
```

`loggedin_test.py` needs the Student role to have Admissions > My Application Forms.
`install_site.py` runs Gibbon's web installer with demo data (it also needs `GIBBON_DB_USER` and
`GIBBON_DB_PASS`).

Expected on stock v30.0.01, for comparison:
- `applicant_scenarios.py` and `scenarios.py` fail the checks this package fixes;
- `housetest.py` shows the house on person 1;
- `loggedin_test.py` makes the student their own Parent 1.
