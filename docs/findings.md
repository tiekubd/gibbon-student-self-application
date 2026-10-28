# Students Applying for Themselves: Findings and Fixes

Oct 24, 2026 · Tieku Bortei-Doku, High Point Education Solutions

One setting per application form, "Who completes this application?", lets a student apply for themselves on Gibbon v30.0.01, including on forms that still collect parent details. It passed every automated check, seven hand tests, and application fee and invoice payments through the PayPal sandbox on a fresh v30.0.01 site with demo data. A third invoice choice, Student, bills the student directly, reading their details live from their own record. Testing also found seven v30 bugs, six still in the development branch.

## The design

Each form says who fills it in, in Form Builder > Active Features > Applicant. Nothing is inferred from which fields a form has.

| Setting | Behaviour |
| --- | --- |
| A parent or guardian, for a student | The default and Gibbon's existing behaviour. Every form never set behaves this way. |
| The student, for themselves | The student is the applicant. Parent sections can stay on the form (contacts, financial aid details); those parents are still created and joined to the family. |

A school that accepts both publishes two forms, named so applicants can tell them apart, such as "Application by a parent or guardian" and "Application by a student". Gibbon's admissions page already lists every active form by name and description.

Inferring "student applicant" from missing parent fields was tried first and dropped: some institutions have the student apply but still collect parent information. A third option, "let the applicant choose" with a question on the form, was built and also dropped, in favour of separate forms.

The rule lives in one class, `ApplicantType`, and every automated step follows it:

- **Submission email:** to the admissions account, plus the applicant's own email if different (Parent 1's or the student's). The greeting names the applicant.
- **Processing fee request:** to the applicant, same greeting.
- **Admissions account:** on acceptance, linked to Parent 1 when a parent applied, or to the student when the student applied.
- **Student email:** pre-filled from the account email when the student applies.
- **Parent 1:** filled from the account only when a parent applies, so a student is never recorded as their own parent.
- **Acceptance:** the Parent Acceptance Template is optional; "inform parents" only appears when the form has parent fields.

## Findings

Seventeen of 21 findings are fixed in the package; two are school settings; two are open (checking a family-less applicant's Family choice, and reusing records on a repeat application).

| # | Finding | Status |
| --- | --- | --- |
| 1 | The processing fee can never run on a form without `parent1email` | Fixed |
| 2 | Payment offers only Family or Company; there is no "myself" | Fixed (Myself on student forms) |
| 3 | The submission email greets "Dear ," when there is no parent, and passed a boolean instead of Parent 1's address | Fixed |
| 4 | A form without parents cannot save its config without a Parent Acceptance Template; the accept page offers to inform parents | Fixed |
| 5 | The admissions account is linked to the family, never to the student | Fixed |
| 6 | The applicant's own email is replaced by `[username]@localhost.test` and moved to Email Alternate | Setting (`newStudentDetails`) |
| 7 | Invoice recipients never include the student | Fixed (invoiceTo = Student) |
| 8 | The Company workaround copies the student's details into four fields, which drift | Fixed (Student reads the record live) |
| 9 | With Create Family off, the account is linked to nobody | Fixed (linked to the student) |
| 10 | A family-less applicant can choose "Family" for invoices; nothing checks it | Open (Myself is now the default on student forms) |
| 11 | "No parent fields" is the wrong signal for "the student is applying" | Fixed (explicit setting) |
| 12 | A logged-in student applying again is silently made their own Parent 1 | Fixed |
| 13 | An acceptance email issue, reported privately to the Gibbon team; details withheld until a fix is released | Fixed |
| 14 | Family page fails for an account with a family but no person: a fatal error for staff, or hidden address fields still required | Fixed; reported in [#2183](https://github.com/GibbonEdu/core/issues/2183) |
| 15 | The "Submission Email" line is missing from the applicant's results page on forms without a Parent 1 email | Fixed; reported in [#2184](https://github.com/GibbonEdu/core/issues/2184) |
| 16 | Auto House Assign writes every new student's house to person 1 | Fixed; fixed upstream for v31 |
| 17 | Students lack "My Application Forms", so a student who logs in as the admissions page asks cannot find the form | Setting (Manage Permissions) |
| 18 | Applying again creates a second student record, and re-entered parents become new records | Open (Phase 2b) |
| 19 | The receipt for an invoice paid online has a blank status, the wrong receipt number and no payment details when the payer is logged in | Fixed; reported in [#2201](https://github.com/GibbonEdu/core/issues/2201) |
| 20 | The receipt for a Company invoice paid online goes to the family, not the company | Fixed; reported in [#2202](https://github.com/GibbonEdu/core/issues/2202) |
| 21 | The Admissions Family tab shows an empty "New Parent" row on forms without Parent 1, and labels the applicant as their own sibling | Fixed; reported in [#2207](https://github.com/GibbonEdu/core/issues/2207) |

- **#12:** a logged-in user's own record becomes Parent 1 through a hidden field. Right for a parent, wrong for an accepted student applying again. Reproduced on stock v30.0.01.
- **#14:** `FamilyFields` hides the address fields on one test (person or family) but validates them on another (person only), and only sets `$families` in one branch. Reproduced on stock in staff Edit.
- **#15:** the view looks for `submissionEmail` in form data, but it is recorded as a result. Staff see the line because their view is read-only.
- **#18:** for a student, a second application is always the same person (next intake, another programme, postgraduate study), but Gibbon treats each one as a new child.
- **#19:** `invoices_payOnlineProcess.php` passes the payment count where `receiptContents()` expects a zero-based receipt number, and counts payments with an inner join to `gibbonPerson`, so payments by someone not logged in are left out. A logged-in payer's receipt looks for a payment that doesn't exist; a payer who isn't logged in gets the right receipt for a first payment by chance, but receipt 1 again for any later one. Affects every school taking online invoice payments.
- **#20:** `invoices_payOnlineProcess.php` line 156 has `$invoiceTo = ''` (an assignment) inside the check that the invoice was found, so `$invoiceTo` is always empty afterwards and the receipt goes down the family branch. Affects every school whose company-billed invoices are paid online.
- **#21:** `queryFamilyByApplication()` in `AdmissionsApplicationGateway.php` shows Parent 1 from the application data without checking there is any (Parent 2 already checks `parent2surname`), and labels every application on the account "Sibling", including the one being viewed. Found on a university graduate form with no parent fields; the label also shows on parent forms.

## Pre-fill and logging in

Two behaviours that look like gaps are Gibbon's design, unchanged here.

- **Typing an email that already has an account** starts a new application but shows no earlier data, since anyone could type someone else's email. Pre-fill follows "Continue an Existing Application Form" and the emailed link, or logging in.
- **The student's own details are not pre-filled** on a second application, because the Sample form marks only family, parent and payment fields for pre-fill. A school can mark student fields in Form Builder.

The admissions page asks existing users to log in first "to prevent creation of duplicate data". That holds for parents; for students it needs #17 and #18 first.

## Application fees and invoices

Tested with the PayPal sandbox on the live test site (Gibbon's `Payment` class needed a local change to reach the sandbox; it isn't part of the package).

- **Application fees** don't depend on the "Send Future Invoices To" choice. Payment on Submission and the Processing Fee both worked on the student form (the Processing Fee only with the package, #1) and on the parent form, and each payment was recorded against the application.
- **Who gets what:** the processing fee request goes to the applicant (the student, or Parent 1), but receipts always go to the admissions account email, as on stock. On a parent form where the account email and Parent 1 differ, the request and the receipt reach different people.
- **Invoices after acceptance,** with a Family invoicee: offered only to family adults, so a student who applied for themselves can't be chosen (#7). With the Company workaround: the invoice reached the student, by copying their name into both company fields and their address by hand (#8).
- **The student's own email** was the `username@localhost.test` placeholder under the default New Student Details (#6), so a future "Student" invoice option needs that setting changed, or the applicant's real email kept as the primary one.

## Billing the student (Phase 3)

A third choice, **Student**, beside Family and Company. It adds the value `Student` to `invoiceTo` in three tables (one SQL step, with a rollback) and a Student branch wherever Gibbon chooses between Company and Family:

| Where | With Student |
| --- | --- |
| Application form, student forms only | "Send Future Invoices To" offers Myself (selected), Family, Company |
| Acceptance | Invoicee created as Student, no company details |
| Manage Invoicees, Data Updater | Student is a third choice |
| Add invoice, activity fees | Invoice billed to Student; every fee goes on it |
| Invoice and receipt | The student's name, email and own address (or the family's), read live |
| Issue, bulk issue, reminders, recorded and online payments | Emailed to the student |

Not included: copying the family on a Student invoice, or splitting fees. Students see their invoices with Gibbon's existing View Invoices_mine permission, off for students by default.

## Workarounds available today

An institution where every applicant is an adult can run on v30 now with configuration alone; a school with both parent and student applicants cannot.

| Workaround | How | Limits |
| --- | --- | --- |
| Company fields as "myself" | Applicant chooses Company and enters their own name, address and email. Tested on stock v30: the invoice email arrived. | Four required fields re-type data Gibbon already holds; copies drift from the student record (#8) |
| String Replacement | System Admin > String Replacement, **Whole** mode: `Company` to `Myself`, plus one entry per label ("Company Name", "Company Emails", and so on) and the help text. Also renames the invoice heading to "Invoice To (Myself)". | Applies system-wide, so wrong for schools that also take parent applications. Partial mode would produce "Myself Name". Labels only: the data duplication remains |
| Database triggers | Copy the student's details into the company fields on insert and update (the approach in the forum thread) | Outside Gibbon's code; invisible to admins; must survive upgrades |
| Form group per program | One form group per year group, so enrolment and invoicing work | Form groups are still required by Finance queries |

## Testing

Every check passed with the package; stock v30.0.01 fails exactly the checks it fixes.

| Test | Where | Result |
| --- | --- | --- |
| 32 applicant checks: student form with parent sections (twice), parent form (two children, and an accepted student for their own child), forms list, Form Builder setting | Fresh v30.0.01 + demo data, over HTTP | 32 / 32 |
| 14 earlier checks: student form without parents, Sample form, adult student as Parent 1 on a parent form | Same | 14 / 14 |
| Email and fee processes against Gibbon's own classes | Harness | 20 / 20 |
| Logged-in student applying again | Same site | Parent 1 is the parent entered; stock makes the student their own Parent 1 |
| Houses | Same site | Every student gets a house; stock writes it to person 1 |
| Install script: check, backup, verify, rollback | Test site and a copy of stock | All work; rollback restores stock exactly |
| Seven hand tests: Form Builder setting, forms list, student with parents, same student again logged in, parent form, student without parents, Sample form | Fresh v30.0.01 + demo data on a live host | All passed |
| Payments: submission and processing fees on both forms; invoices paid online by a Family and a Company invoicee, logged in and not | Same, PayPal sandbox | All recorded; receipt bug (#19) found and reproduced |
| Receipt numbers against Gibbon's own `receiptContents()`, first and second payments, payer logged in and not | Test site | Fixed in every case; stock wrong in three of four |
| Billing the student: application form, acceptance, add, issue, bulk issue, reminder, payment receipt, Manage Invoicees, Data Updater, the student's own view, and a parent-form Family invoicee | Local v30.0.01 + demo data, over HTTP | 34 / 34 |
| Applicant suites rerun with the billing files | Same | 32 / 32, 14 / 14 |
| Hand tests 8 to 13: Myself on the student form only, acceptance as Student, invoice issued to the student, online payment logged out and logged in, a Company receipt (#20), the student's own View Invoices | Live v30.0.01 site, PayPal sandbox | All passed |
| Database step and its rollback, with the install script | Copy of stock v30.0.01 | `verify` refuses until the step is run; rollback restores stock columns, Student rows become Family |

No PHP warnings or errors from Gibbon code in any run.

## Next steps

1. **Upstream discussion** of the setting in the Feature Requests thread, before any pull request.
2. **Bug reports:** #14 filed as [#2183](https://github.com/GibbonEdu/core/issues/2183), #15 as [#2184](https://github.com/GibbonEdu/core/issues/2184), #19 as [#2201](https://github.com/GibbonEdu/core/issues/2201), #20 as [#2202](https://github.com/GibbonEdu/core/issues/2202), #21 as [#2207](https://github.com/GibbonEdu/core/issues/2207), and #13 reported privately.
3. **Phase 2b:** on acceptance, reuse the existing student when the account already belongs to one, and match parents already in the family by email (#17, #18).
4. **Phase 3, Finance:** built (#2, #7, #8); 34 / 34 automated checks, and hand tests 8 to 13 passed on the live site with the PayPal sandbox. Next: the Feature Requests thread.

## Upstream context

Nothing planned upstream conflicts with this work, and the roadmap's Admissions item is the design to fit around, so the next step is a Feature Requests discussion, not a pull request.

- **Roadmap:** the Admissions module is "In Progress": more reporting and statistics, and pre-application and post-application forms.
- **Separate forms:** the two-option design follows the existing advice to create separate application forms for different situations.
- **Development branch (9 Oct 2026):** AssignHouse is fixed ([PR #2121](https://github.com/GibbonEdu/core/pull/2121)); #14, #15, #19 and #20 are still present; #13 is reported privately. On 16 Oct 2026 (commit `65f86bf`), #21 was also present. No change touches the `invoiceTo` columns.
- **Student invoicing:** in 2020 Ross said invoicing students directly was not possible but that he would include it if someone implemented it. Phase 3 is that implementation.
- **Code style:** Sandra's review of PR #2121 asked for a single gateway query instead of several.
- **Dates:** v31 string freeze 20 Oct 2026, release 20 Nov 2026; v32 string freeze 20 Apr 2027. The setting adds new strings, so it would target v32; the bug fixes add none.

## Sources

- [Gibbon Road Map](https://docs.gibbonedu.org/explanation/development/gibbon-road-map)
- [Admissions and billing for adult students](https://ask.gibbonedu.org/t/admissions-and-billing-for-adult-students-feasibility/15478)
- [Admission Form: Student doesn't have Email](https://ask.gibbonedu.org/t/admission-form-student-doesnt-have-email/15261)
- [Gibbon with no parents](https://ask.gibbonedu.org/t/gibbon-with-no-parents/2815)
- [Fee invoices to students](https://ask.gibbonedu.org/t/fee-invoices/2607)
- [PR #2121: house assignment](https://github.com/GibbonEdu/core/pull/2121)
