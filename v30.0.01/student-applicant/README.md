# Students applying for themselves, and billing them directly (Gibbon v30.0.01)

Adds one setting to every application form, in **System Admin > Form Builder > (form) >
Active Features > Applicant**:

**Who completes this application?**

| Choice | Behaviour |
|---|---|
| A parent or guardian, for a student | The default, and Gibbon's existing behaviour. Every form that has never been set behaves this way. |
| The student, for themselves | The student is the applicant. Parent sections can still be on the form (contacts, financial details for scholarships). Those parents are still created and joined to the family. |

**Accepting both kinds of applicant:** create one form of each and name them so applicants can
tell them apart. Gibbon's application page lists every active form by name and description,
for example:

- Application by a parent or guardian: *For parents or guardians applying for a student.*
- Application by a student: *For students applying for themselves. Parent or guardian details are still collected.*

Gibbon's automated steps follow the setting of the form used:

- **Submission email**: goes to the admissions account, plus the applicant's own email if different (Parent 1's, or the student's). The greeting names the applicant.
- **Processing fee request**: goes to the applicant, with the same greeting.
- **Admissions account**: on acceptance, linked to Parent 1 when a parent applied, or to the student when the student applied, so either can return to it.
- **Student email**: pre-filled from the admissions account email when the student is the applicant. It can still be edited.
- **Parent 1**: filled from the admissions account only when a parent is applying. A student applying again is never recorded as their own parent.
- **Acceptance**: the Parent Acceptance Template is optional, and "inform parents" only appears when the form has parent fields.

## Billing the student directly

Gibbon sends invoices to a student's **Family** or to a **Company**. This adds a third choice,
**Student**: invoices go to the student themselves, using their name, email and address from
their own record, read at the time each invoice or receipt is made (nothing is copied).

| Where | With Student |
|---|---|
| Application form, on forms the student completes | "Send Future Invoices To" offers **Myself**, Family or Company, with Myself selected. Parent forms still offer Family or Company. |
| Acceptance | The student's invoicee record is created as Student, with no company details |
| Finance > Manage Invoicees > Edit, and Data Updater > Finance Data | Student is a third choice beside Family and Company |
| Finance > Manage Invoices > Add, and activity fees | The invoice is billed to Student; every fee goes on it |
| The invoice and receipt | "Invoice To (Student)" / "Receipt To (Student)": the student's name, email, and their own address, or their family's home address if they have none |
| Issuing, bulk issuing, reminders, recording a payment, paying online | Emailed to the student's email |

Not included: copying the family on a Student invoice, or splitting fees between the student and
someone else. A school wanting either can keep Family or Company for that student.

Two school settings matter for this:

- **The student's email.** Invoices go to the student's Gibbon email. With the default *New Student Details* on an application form, that becomes `username@localhost.test` and the applicant's real email moves to Email Alternate. Set it so the applicant's own email stays the student's email.
- **Students seeing their invoices.** Grant the Student role Finance > *View Invoices_mine* in User Admin > Manage Permissions. Gibbon already has this permission; it is off for students by default.

This part adds the value `Student` to three database columns, with `sql/finance_student.sql`.
Nothing in the Gibbon v31 development branch changes those columns.

It also fixes these v30.0.01 bugs, found while testing:

- **AssignHouse**: every new student's house was written to person 1 instead. This is already fixed upstream for v31.
- **Family page for a returning student**: when an admissions account has a family but no parent linked (for example, a student applying a second time while logged in), the Family page either crashed ("Undefined variable $families") or hid the address fields but still required them, so it could never be submitted.
- **Submission results**: on the page an applicant sees after submitting, the "Submission Email: An email was sent to …" line only appeared on forms with a Parent 1 email, so on a student form it was missing even though the email was sent. (Staff viewing the application did see it.)
- **An acceptance email issue**: reported privately to the Gibbon team; details withheld until a fix is released.
- **Online invoice payment receipts, who they go to**: a Company invoice paid online had its receipt sent to the family, not the company. `invoices_payOnlineProcess.php` line 156 assigns (`$invoiceTo = ''`) where it means to compare, which clears the invoice's "billed to" before the receipt is sent. Reported in [#2202](https://github.com/GibbonEdu/core/issues/2202).
- **Online invoice payment receipts**: when the payer was logged in, the receipt email had a blank status, the wrong receipt number and no payment details. A payer who wasn't logged in got a correct receipt for a first payment, but receipt 1 again for any later payment on the same invoice. Reported in [#2201](https://github.com/GibbonEdu/core/issues/2201).

The applicant setting needs no database change; it is stored in the form's existing configuration. Billing the student needs `sql/finance_student.sql` (below).

## Install (from the Gibbon webroot, v30.0.01 only)

Back up the database and the files first.

1. Upload `student-applicant.sh` to the webroot and run `bash student-applicant.sh check`.
   All 31 lines should say `OK` (stock v30.0.01; `ApplicantType.php` is new, so `OK` there means it isn't present yet). Stop if any say `UNEXPECTED`.
   The last line shows whether the database step has been done.
2. Run `sql/finance_student.sql` one step at a time (phpMyAdmin, or `mysql` on the server), checking each result.
3. Run `bash student-applicant.sh backup`. It copies each file to `<file>.v30bak`.
4. Upload the `src` and `modules` folders over the webroot. That's 31 files, one of them new: `src/Forms/Builder/ApplicantType.php`.
5. Run `bash student-applicant.sh verify`. All 31 should say `OK`, and the database line `done`.

The database step comes before the files: with the files but not the database, choosing Student
would fail when it is saved.

Already installed an earlier version of this package? Run `check` first: the files already updated
show `ALREADY`. Then the database step, `backup` (existing `.v30bak` copies are left as they are),
upload, and `verify`.

Rollback: `bash student-applicant.sh rollback`, then `sql/finance_student_rollback.sql`, which
switches anything billed to Student back to Family before removing the value.

| File | Before (stock v30.0.01) | After |
|---|---|---|
| modules/Admissions/applicationForm.php | `2cb8e503612ab106e2628d847a6fdd28` | `93f30dcaa61f13bb4e8a5036ab672a94` |
| modules/Admissions/applicationFormProcess.php | `d664a7f0821907eee242ee98e377df13` | `ae06f4c68d4797039cc0fce2d63a761a` |
| modules/Admissions/applications_manage_accept.php | `f0f15ae6133481af7a9c71a3761a925b` | `b30a4c1010b90f5bec379db201a8dc93` |
| modules/Admissions/applications_manage_acceptProcess.php | `94a60123ecc76725d55017164035cd8b` | `febbc24d90034fd2c7b9dad40b7a181c` |
| modules/Admissions/applications_manage_add.php | `feab3e6c973bad1f385f731ddf620442` | `96c08e0b65c7f855e858728c41d337c4` |
| modules/Admissions/applications_manage_addProcess.php | `9caf3fd870ab264a464c0b3dbedbcda0` | `7b20e60dd4be699c8773baffcdf5b5ae` |
| modules/Admissions/applications_manage_edit.php | `f5634305bdde1aec3819eb8f6ca64291` | `2c74b515e3fcb56d655982668be2eac3` |
| modules/Admissions/applications_manage_editProcess.php | `c68edc88f86bd757b097ef991666a83f` | `ecb33f8bd3c68dc5defbb85f11e6d1de` |
| src/Forms/Builder/ApplicantType.php | (new) | `62106efe8b6081fdffa9be61a3d2ed2e` |
| src/Forms/Builder/Fields/FamilyFields.php | `c588ad5c7d7c6869bbb661b791356dc4` | `696acc9557cd57279404ebf19c1e189b` |
| src/Forms/Builder/Fields/FinanceFields.php | `ac1364b614f1e8e1e7009e43bba616e6` | `a8ec5b42bc116d2364e0c6ddc737fbfb` |
| src/Forms/Builder/FormPrefill.php | `bd798ce3cc756b33169dd3ab0a4b26e3` | `0fd469b5499fafd6c85086f401d7e3a7` |
| src/Forms/Builder/Process/ApplicationSubmit.php | `dc5cf5f4827419c599f58edd9901ab99` | `89d9c0fe256019c10a2f598667b34948` |
| src/Forms/Builder/Process/AssignHouse.php | `79aa45d3413d2d0b9795576fb52b1a25` | `0149bd714156aafe7ed29b8a17bec2b7` |
| src/Forms/Builder/Process/CreateInvoicee.php | `63efd961031f16c6ef1f03b26e4df623` | `e59aba3af49d453c0a1bc824fb27e1b6` |
| src/Forms/Builder/Process/PayProcessingFee.php | `867bf80c84a085a663de5ca6632e0c7d` | `4aef44e5baf660f20bde50504dc97877` |
| src/Forms/Builder/Process/SendAcceptanceEmail.php | `d6952df5cc9f3845c608052e7103b4e4` | `e0da356866fec91af5cc4145f51df5ce` |
| src/Forms/Builder/Process/SendSubmissionEmail.php | `6e3f32c8ca52a177e2b447102a1124bf` | `4800a6bd8b7fbf33cbd14bdb8e52ba7e` |
| src/Forms/Builder/View/ApplicationSubmitView.php | `8fc1e2ef147346291af8d9222f4de602` | `aca4f0fcfe35d428df1f502c340f624d` |
| src/Forms/Builder/View/PayProcessingFeeView.php | `97ce0898be485aa066b0e942b31e7563` | `98abd13cfbb5f4b9057de964da28c006` |
| src/Forms/Builder/View/SendAcceptanceEmailView.php | `46e805c62f5930c482fe64abc1fce1e0` | `a590a907956f52a0ccdb293cf15a135f` |
| src/Forms/Builder/View/SendSubmissionEmailView.php | `4779fd87ac6a5accb5b5df00ffd493b9` | `4a95e399308218caaaefd22042e1118c` |
| modules/Activities/activities_paymentProcessBulk.php | `d925ed21c3b2806b9f07d6d6683ddb52` | `825e9d285ddbf84e40b78c9a4ef65f18` |
| modules/Data Updater/data_finance.php | `ac784758877e9934c9ee87cbe3c95fc1` | `075461dafa65397afef0bd0ca2785b4f` |
| modules/Finance/invoicees_manage.php | `37c8e95aa6f4f0e4fe12bf9fc4a9552e` | `007b8f588e73d22eaea69997d7a9ceb0` |
| modules/Finance/invoicees_manage_edit.php | `ce57e7853ca1ec979a0c1a31439881bc` | `b8a3dc9fd8474eade99e06fe891d8d4b` |
| modules/Finance/invoices_manage_addProcess.php | `d1d960ebfb70a988cb48ab4dd2e6699a` | `d47fc872246428f9daa507807e2f614a` |
| modules/Finance/invoices_manage_processBulk.php | `34dc4a1138defb4b33d54472512ae3ef` | `cb30cd3dc62f277831ab6a63d75aeab7` |
| modules/Finance/invoices_payOnlineProcess.php | `0cabab29237de8170156d641276e2994` | `0e29707fc475249ba131ad68de5da3ff` |
| modules/Finance/moduleFunctions.php | `aa50a8b8c9e1ecbd33acb8b6c8a161bd` | `6aab0928fbb4d9631631922ac5a8b8df` |
| modules/Finance/src/Forms/FinanceFormFactory.php | `3e8c1990a5046beeda76f18476bd66cb` | `fedb950fc48e900e33dbec838f850d4c` |

## Test forms (test site only)

`sql/test_forms.sql` makes the Sample Application Form active and public, then creates three
copies of it. Run it one step at a time and check each step's result:

| Form | Setting |
|---|---|
| Sample Application Form (000001) | Not set, so parent |
| Student Self-Application (000002) | The student, for themselves; no parent or Family pages |
| Application by a student (000003) | The student, for themselves; parent sections kept |
| Application by a parent or guardian (000004) | A parent or guardian, for a student (saved explicitly) |

The last two are the pair a school accepting both kinds of applicant would publish.

## Testing by hand

Use a new email address for each applicant. This query shows who each admissions account is linked to:

```sql
SELECT a.email, p.preferredName, p.surname, r.category
FROM gibbonAdmissionsAccount a
LEFT JOIN gibbonPerson p ON p.gibbonPersonID = a.gibbonPersonID
LEFT JOIN gibbonRole r ON r.gibbonRoleID = p.gibbonRoleIDPrimary
ORDER BY a.gibbonAdmissionsAccountID DESC LIMIT 10;
```

1. **Form Builder.** The Sample Application Form shows "A parent or guardian, for a student", and "Application by a student" shows "The student, for themselves". There are two choices.
2. **Application page.** Both "Application by" forms are listed with their descriptions.
3. **A student applies on "Application by a student".**
   - The student email is pre-filled with the account email.
   - Fill in a parent with a different email.
   - The confirmation goes to the student only and greets the student.
   - After acceptance, the student, parent and family are created, the account is linked to the student, and the student has a house.
4. **The same student applies again, logged in.** An accepted student has a Gibbon login, and logging in is the route Gibbon's own message asks existing users to take. Students need the "My Application Forms" permission first (see below).
   - Log in as the student and go to People > Admissions. Under New Application Form, choose "Application by a student".
   - The Family page shows the student's family to choose (no crash), and Parent 1 is filled from the last application and editable. It is not replaced by the student.
   - The page submits.
   - After acceptance, Parent 1 is the parent entered, not the student, and the account is still linked to the student. A second student record is created (see the known limitation).

   Applying again without logging in (typing the same email on the Admissions page) also works, but Gibbon shows no earlier data that way until the applicant proves they own the email, through "Continue an Existing Application Form" and the emailed link.
5. **A parent applies on "Application by a parent or guardian".**
   - The student email is not pre-filled.
   - The confirmation goes to the parent and greets the parent.
   - After acceptance, the account is linked to Parent 1.
   - When the same parent applies for a second child, they are Parent 1 again.
6. **A student applies on Student Self-Application.** As test 3, but no parent is created.
7. **The Sample Application Form.** Behaves exactly as stock Gibbon.

### Billing the student (tests 8 to 13)

For online payment, set up a payment gateway (a PayPal sandbox works) and Finance Settings > Enable Online Payment. Accept each student with a form group, so they are enrolled and can be invoiced.

8. **Myself on the form.** On "Application by a student", the Final page's "Send Future Invoices To" shows Myself (selected), Family and Company. On "Application by a parent or guardian" it shows Family and Company only.
9. **Acceptance.** Accept the student who chose Myself. Finance > Manage Invoicees shows them as Student; Edit shows Student selected, beside Family and Company.
10. **Invoice.** Manage Invoices > Add an invoice for them, then Issue. Email Invoice lists only the student (and CC Self). The email says "Invoice To (Student)" with the student's name and email, not a parent.
11. **Paying online.** Pay the invoice from its email, once logged out (a private window) and once logged in. Each receipt goes to the student and shows "Receipt To (Student)", Paid (Complete), receipt number 1, and the payment.
12. **Company receipts.** For a student set to Company, pay an invoice online. The receipt goes to the company email, not the family.
13. **The student's view.** Grant Student "View Invoices_mine", log in as the student: Finance > View Invoices lists their invoices.

### Letting students apply while logged in

By default only Parent, Teacher and Support Staff have the Admissions "My Application Forms" permission. Grant it to Student in User Admin > Manage Permissions if accepted or current students should apply again while logged in. Gibbon's "please log in now to prevent creation of duplicate data" message on the Admissions page is written for parents. For a student, logging in attaches the application to their own account, but a second student record is still created on acceptance (see the known limitation). Schools can say what students should do in each form's description.

## Tested

Tested on a fresh install of the official v30.0.01 release bundle with demo data (PHP 8.3, MariaDB). The package was installed with its own script, the test forms above were created, and the real pages were driven over HTTP:

- 32 / 32 applicant checks:
  - the student form with parent sections, first and second application;
  - the parent form: a first child, a second child, and an accepted student applying for their own child;
  - both forms listed on the application page;
  - the Form Builder setting.
- 14 / 14 earlier checks:
  - Student Self-Application;
  - the Sample Application Form;
  - an accepted student applying for their own child on a parent form becomes Parent 1.
- 20 / 20 checks of the email and fee processes against Gibbon's own classes.
- A logged-in returning student (Student role granted "My Application Forms"): the Family page offered their family and submitted. After acceptance, Parent 1 was the parent entered and the account stayed with the student. On stock v30.0.01 the same steps made the student their own Parent 1.
- Houses: all 11 students accepted with these files got a house, and person 1 was untouched.
- Rollback restored stock v30.0.01. Stock fails the checks this fixes, its 11 accepted students got no house (each was written to person 1), and the parent-form checks pass on it too, so parent behaviour is unchanged.
- Application fees and invoices with the PayPal sandbox on a live v30.0.01 site: the submission and processing fees on both the student and the parent form, and invoices paid online by a Family invoicee and by a student set up as Company. The receipt check was then run against Gibbon's own receipt code: with the fix, logged-in and logged-out payers both get the right receipt, including a second payment on the same invoice.
- Billing the student: 34 / 34 checks with `tests/end-to-end/finance_scenarios.py`, on the same site after `sql/finance_student.sql`:
  - the student form offers Myself, selected; the parent form still offers Family and Company;
  - acceptance creates a Student invoicee with no company details;
  - an invoice billed to Student; issuing, bulk issuing, a reminder and a recorded payment each email the student only, with "Invoice To (Student)" or "Receipt To (Student)" and the family's address;
  - Manage Invoicees and Data Updater offer Student and save it; the student sees their invoices with View Invoices_mine;
  - a parent-form applicant is still Family, invoiced to the parent.
- The applicant suites above, rerun with the billing files installed: 32 / 32 and 14 / 14. The receipt-number test passes.
- Install script with the database step, on a copy of stock v30.0.01: `check` reports the database step as "not run", `verify` refuses until it is run, and `rollback` plus `sql/finance_student_rollback.sql` restore stock files and columns (anything billed to Student becomes Family).
- Hand tests 8 to 13 on a live v30.0.01 site with the PayPal sandbox: all passed. A Student invoice paid online, logged out and logged in, gave the student a complete receipt; a Company invoice's receipt reached the company email (stock sent it to the father); the student saw both invoices under View Invoices.
- No PHP warnings or errors from Gibbon code.

Known limitation (as in stock Gibbon): accepting a second application from the same student
creates a second student record.
