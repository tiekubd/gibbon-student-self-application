# Student Self-Application: Findings and Fixes

Oct 10, 2026 · Tieku Bortei-Doku, High Point Education Solutions

A student can already apply to Gibbon v30.0.01 without parent fields and be accepted cleanly, but testing found ten gaps. Phases 1 and 2 close the admissions gaps and are confirmed live on v30.0.01; billing the student directly (Finance) still needs agreement upstream.

## Test setup

The test form "Student Self-Application" is a copy of the Sample Application Form with the Family page removed, the home address fields moved to the Student page, student email required, `createParents = N`, and the parent acceptance email settings removed. It was built by SQL script on a Gibbon v30.0.01 test instance.

| Run | Applicant | Config | Payment choice | What it tested |
| --- | --- | --- | --- | --- |
| A | Mark Spencer | `createFamily = Y` | Family | Default path: submit, accept, invoice |
| B | Ama Mensah | `createFamily = N` | Family | Acceptance with no family at all |
| C | Mark Spencer (invoicee edited) | n/a | Company, filled with the student's own details | The Company-fields workaround from the forum thread |

Related discussion: [Admissions and billing for adult students](https://ask.gibbonedu.org/t/admissions-and-billing-for-adult-students-feasibility/15478).

## Findings

Three findings (#1, #3, #4) are small form builder fixes and one (#6) is configuration; the account link (#5, #9) and Finance (#2, #7, #8, #10) are the structural ones.

| # | Finding | Evidence | Code location | Phase |
| --- | --- | --- | --- | --- |
| 1 | Processing fee can never run on a student-only form: it requires `parent1email` | Form Builder lists it under Inactive Features: "Payment Gateway, parent1email" | `src/Forms/Builder/Process/PayProcessingFee.php`, `verify()` | 1 |
| 2 | Payment choice offers only Family or Company; help text speaks of "your family's contact preferences" | Application form, Final Details page | `src/Forms/Builder/Fields/FinanceFields.php`; `gibbonFinanceInvoicee.invoiceTo` enum | 3 |
| 3 | Submission email greets "Dear ," | Confirmation email for application 1 | `SendSubmissionEmail.php`: template data only passes `parent1title`, `parent1preferredName`, `parent1surname` | 1 |
| 4 | A student-only form cannot save its config without choosing a Parent Acceptance Template; the accept page then offers to inform parents | Template `000012` reappeared after Step 1 removed it; "inform parents" checkbox on accept page | `src/Forms/Builder/View/SendAcceptanceEmailView.php`, `->required()` on `acceptanceEmailParentTemplate` | 1 |
| 5 | Admissions account links to the family, never to the student | Account 1: `gibbonPersonID` NULL, `gibbonFamilyID` 854 | `modules/Admissions/applications_manage_acceptProcess.php`: only `gibbonPersonIDParent1` is linked | 2 |
| 6 | The applicant's real email is replaced by the default `[username]@localhost.test` and moved to Email Alternate | Mark: `mspencer@localhost.test` / `applicant@example.com` | `newStudentDetails` config (configuration, not code) | config |
| 7 | Invoice recipients come only from Company, family adults, or CC Self; the student is never a candidate | Issue screen: "There are no family members available to send this receipt to." | `modules/Finance/src/Forms/FinanceFormFactory.php`, `createInvoiceEmailCheckboxes`; sending in `modules/Finance/moduleFunctions.php` | 3 |
| 8 | The Company workaround duplicates the student's details into four required fields, which drift | Invoice shows 100 Main St; application said 200 Main St | Same as #7 | 3 |
| 9 | With `createFamily = N` the admissions account is linked to nobody | Account 2: `gibbonPersonID` and `gibbonFamilyID` both NULL | Same as #5 | 2 |
| 10 | A family-less applicant can choose "Family" for invoices; nothing checks it | Invoicee 393: `invoiceTo = Family`, student in 0 families | `CreateInvoicee.php` | 3 |

Also spotted in source, not yet triggered: `SendSubmissionEmail` calls `AddAddress($formData->has('parent1email'))`, passing a boolean instead of the address.

## Predictions that turned out wrong

More already works without parents than the source suggested at first glance.

- **Submission email does send.** It requires `email` *or* `parent1email` (`requiredFieldLogic = 'ANY'`) and always goes to the admissions account email. Only the greeting is broken (#3).
- **Family naming falls back to the student.** `CreateFamily::generateFamilyName()` uses the student's preferred name and surname when there are no parents, giving "Mark Spencer".
- **Acceptance email works for the student.** `SendAcceptanceEmail` also uses `ANY` logic; the welcome email reached the student.
- **"Could not be enrolled" is not a parent issue.** `EnrolStudent` returns early when no form group is chosen, on any form.

## Workarounds available today

An institution where every applicant is an adult can run on v30 now with configuration alone; a school with both parent and student applicants cannot.

| Workaround | How | Limits |
| --- | --- | --- |
| Company fields as "myself" | Applicant chooses Company and enters their own name, address and email. Proven in Run C: the invoice email arrived. | Four required fields re-type data Gibbon already holds; copies drift from the student record (#8) |
| String Replacement | System Admin > String Replacement, **Whole** mode: `Company` to `Myself`, plus one entry per label ("Company Name", "Company Emails", and so on) and the help text. Also renames the invoice heading to "Invoice To (Myself)". | Applies system-wide, so wrong for schools that also take parent applications. Partial mode would produce "Myself Name". Labels only: the data duplication remains |
| Database triggers | Copy the student's details into the company fields on insert and update (the approach in the forum thread) | Outside Gibbon's code; invisible to admins; must survive upgrades |
| Form group per program | One form group per year group, so enrolment and invoicing work | Form groups are still required by Finance queries |

## Phases 1 and 2

Phase 1 makes the form builder applicant-aware, with no schema change; Phase 2 links the account to the student and Phase 3 adds a Student option to Finance.

1. Done: no `applicantType` setting after all. Each process decides from the form itself (parent fields present or not), so a setting can never contradict the fields.
2. Done: `PayProcessingFee` sends to `parent1email`, else the student's `email`, else the account email, and becomes available on student-only forms (#1).
3. Done: `SendSubmissionEmail` and `PayProcessingFee` fill the greeting from the student when no parent was collected; existing templates unchanged (#3). The `AddAddress(true)` bug is fixed.
4. Done: Parent Acceptance Template is optional; "inform parents" only appears on forms with `parent1email`; `SendAcceptanceEmail` skips parent emails with no template (#4).
5. Done in Phase 2 (below), with a guard, because `applications_manage_acceptProcess.php` treats an account's `gibbonPersonID` as Parent 1 on later applications, so linking the account to the student (#5, #9) would otherwise make a returning student their own parent.
6. Phase 3, for upstream discussion: `invoiceTo = 'Student'` reading name, address and email live from `gibbonPerson`; a "Myself" payment option; a Student branch in the recipient builder and sender (#2, #7, #8, #10).

Phase 1 was checked with a 17-case harness against v30.0.01's own classes: all pass on the new files; on the originals, 9 fail, reproducing "Dear ,", the boolean recipient and the unsent fee request, while every parent-form case passes on both.

Phase 2 (built, tested locally, confirmed live on the v30.0.01 test instance): on forms without parent fields, acceptance links the admissions account to the student, and Student Contact > Email is pre-filled from the account email. The account's person is never treated as Parent 1 when the form has no parent fields and that person is a Student, so a returning student is not recorded as their own parent; on a parent form an accepted student is Parent 1. Tested end to end on the official v30.0.01 bundle: 14 / 14 checks pass; 10 / 14 on stock v30; linking without the guard makes the student their own Parent 1. Known limitation, unchanged from v30: a second accepted application creates a second student record.

## Related bug: Auto House Assign (v30.0.01)

In v30.0.01 every accepted student's house is written to person 1 (usually the first admin), and the student gets none. `AssignHouse` passes `$formData->has('gibbonPersonIDStudent')` (true, read as ID 1) to `userGateway->update()` in both `process()` and `rollback()`. It affects every v30 school using Auto House Assign, with or without these changes.

- Already fixed upstream in the development branch, as part of the sibling-aware house assignment ([PR #2121](https://github.com/GibbonEdu/core/pull/2121)); no report needed.
- For v30.0.01: a two-word hotfix (`has` to `get`), reproduced and verified on the release bundle, plus a repair script that restores each accepted student's house from their application result.
- On the test instance: six students repaired, person 1's house cleared, and a new acceptance confirmed the student gets the house.

## Upstream context

Nothing planned upstream conflicts with this work, but the roadmap's Admissions item is the design to fit around, so the next step is a Feature Requests post, not a pull request.

- **Roadmap:** the Admissions module is "In Progress": more reporting and statistics, and "the ability to handle pre-application and post-application forms". No version given. Feature requests go in the forum's Feature Requests category.
- **v31 code (development branch):** only three overlaps with the files changed here, none conflicting: a milestones warning on the accept page, a `require` path change in the accept process, and the house rework above. The other eight files are identical to v30.0.01.
- **Optional admissions email:** in May 2025 Sandra said she would look at making the admissions account email optional for staff-entered applications. Not landed yet; Phase 2's pre-fill simply does nothing without an account email.
- **Student invoicing:** in 2020 Ross said invoicing students directly was not possible but that he would include it if someone implemented it.
- **Code style:** Sandra's review of PR #2121 asked for a single gateway query instead of several. The upstream version of Phase 2's role check should follow that.
- **Dates:** v31 string freeze 20 Oct 2026, release 20 Nov 2026; v32 string freeze 20 Apr 2027. Changes with new wording (Phase 1.1 text, a "Myself" option, Finance) would target v32.

## Sources

- [Gibbon Road Map](https://docs.gibbonedu.org/explanation/development/gibbon-road-map)
- [Admissions and billing for adult students](https://ask.gibbonedu.org/t/admissions-and-billing-for-adult-students-feasibility/15478)
- [Admission Form: Student doesn't have Email](https://ask.gibbonedu.org/t/admission-form-student-doesnt-have-email/15261)
- [Gibbon with no parents](https://ask.gibbonedu.org/t/gibbon-with-no-parents/2815)
- [Fee invoices to students](https://ask.gibbonedu.org/t/fee-invoices/2607)
- [PR #2121: house assignment](https://github.com/GibbonEdu/core/pull/2121)
