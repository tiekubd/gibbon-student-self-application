# Students applying for themselves (Gibbon v30.0.01)

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

It also fixes these v30.0.01 bugs that affect these applications:

- **AssignHouse**: every new student's house was written to person 1 instead. This is already fixed upstream for v31.
- **Family page for a returning student**: when an admissions account has a family but no parent linked (for example, a student applying a second time while logged in), the Family page either crashed ("Undefined variable $families") or hid the address fields but still required them, so it could never be submitted.
- **Submission results**: on the page an applicant sees after submitting, the "Submission Email: An email was sent to …" line only appeared on forms with a Parent 1 email, so on a student form it was missing even though the email was sent. (Staff viewing the application did see it.)
- **Welcome emails sent to the wrong people**: on acceptance, each welcome email also went to everyone emailed before it, so a parent's username and password reached the student (and Parent 2's reached Parent 1). Still present in the development branch as of 9 October 2026.

No database changes. The setting is stored in the form's existing configuration.

## Install (from the Gibbon webroot, v30.0.01 only)

1. Upload `student-applicant.sh` to the webroot and run `bash student-applicant.sh check`.
   All 20 lines should say `OK` (stock v30.0.01; `ApplicantType.php` is new, so `OK` there means it isn't present yet). Stop if any say `UNEXPECTED`.
2. Run `bash student-applicant.sh backup`. It copies each file to `<file>.v30bak`.
3. Upload the `src` and `modules` folders over the webroot. That's 20 files, one of them new: `src/Forms/Builder/ApplicantType.php`.
4. Run `bash student-applicant.sh verify`. All 20 should say `OK`.

Rollback: `bash student-applicant.sh rollback`.

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
| src/Forms/Builder/FormPrefill.php | `bd798ce3cc756b33169dd3ab0a4b26e3` | `0fd469b5499fafd6c85086f401d7e3a7` |
| src/Forms/Builder/Process/ApplicationSubmit.php | `dc5cf5f4827419c599f58edd9901ab99` | `89d9c0fe256019c10a2f598667b34948` |
| src/Forms/Builder/Process/AssignHouse.php | `79aa45d3413d2d0b9795576fb52b1a25` | `0149bd714156aafe7ed29b8a17bec2b7` |
| src/Forms/Builder/Process/PayProcessingFee.php | `867bf80c84a085a663de5ca6632e0c7d` | `4aef44e5baf660f20bde50504dc97877` |
| src/Forms/Builder/Process/SendAcceptanceEmail.php | `d6952df5cc9f3845c608052e7103b4e4` | `fc88a6c9a8877ec1eb86f02e362a824c` |
| src/Forms/Builder/Process/SendSubmissionEmail.php | `6e3f32c8ca52a177e2b447102a1124bf` | `4800a6bd8b7fbf33cbd14bdb8e52ba7e` |
| src/Forms/Builder/View/ApplicationSubmitView.php | `8fc1e2ef147346291af8d9222f4de602` | `aca4f0fcfe35d428df1f502c340f624d` |
| src/Forms/Builder/View/SendSubmissionEmailView.php | `4779fd87ac6a5accb5b5df00ffd493b9` | `4a95e399308218caaaefd22042e1118c` |
| src/Forms/Builder/View/PayProcessingFeeView.php | `97ce0898be485aa066b0e942b31e7563` | `98abd13cfbb5f4b9057de964da28c006` |
| src/Forms/Builder/View/SendAcceptanceEmailView.php | `46e805c62f5930c482fe64abc1fce1e0` | `a590a907956f52a0ccdb293cf15a135f` |

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
   - Accept with both "inform" boxes ticked. The student's welcome email goes only to the student, and the parent's welcome email (with her login) goes only to the parent.
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
- Welcome emails, accepted with both "inform" boxes ticked: the student, Parent 1 and Parent 2 each received only their own. Stock sent Parent 1's login to the student, and Parent 2's to both.
- Houses: all 11 students accepted with these files got a house, and person 1 was untouched.
- Rollback restored stock v30.0.01. Stock fails the checks this fixes, its 11 accepted students got no house (each was written to person 1), and the parent-form checks pass on it too, so parent behaviour is unchanged.
- No PHP warnings or errors from Gibbon code.

Known limitation (as in stock Gibbon): accepting a second application from the same student
creates a second student record.
