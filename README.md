# Gibbon: students applying for themselves

Work towards letting a student apply to a [Gibbon](https://gibbonedu.org) school or
university **for themselves**, alongside the existing parent-led application process.
Built and tested on **Gibbon v30.0.01**. This is not an official Gibbon release: it is shared
as evidence for a discussion with the Gibbon maintainers, and as tested patches for v30.0.01.

**Start here:** [docs/findings.md](docs/findings.md): what works today, the ten gaps found,
what was fixed, workarounds, and how this relates to the Gibbon roadmap.

## The rule throughout

New behaviour only applies when an application form **has no parent fields**. Forms that
collect Parent 1 / Parent 2 behave exactly as in v30.0.01, and every change was regression
tested against parent forms.

## What's here

| Folder | What it is |
|---|---|
| [`v30.0.01/phase1`](v30.0.01/phase1) | 6 files. Emails and processing fee work without a parent (greeting uses the student; fee goes to the student); Parent Acceptance Template optional; "inform parents" only on parent forms. Also fixes `AddAddress(true)`, which stopped Parent 1 receiving the confirmation copy. |
| [`v30.0.01/phase2`](v30.0.01/phase2) | 4 files, needs Phase 1. Links the admissions account to the accepted student, pre-fills the student's email from the account email, and never records a returning student as their own Parent 1. |
| [`v30.0.01/hotfix-assignhouse`](v30.0.01/hotfix-assignhouse) | 1 file + repair SQL. v30.0.01 writes every new student's house to person 1. Already fixed upstream for v31; this is the same fix for v30. Independent of the other folders. |
| [`patches`](patches) | The same changes as unified diffs against v30.0.01. |
| [`sql`](sql) | Creates the "Student Self-Application" test form from the Sample Application Form. |
| [`tests`](tests) | The test harness and end-to-end scenarios used to verify the changes. |

Each folder under `v30.0.01/` mirrors Gibbon's own layout (`src/...`, `modules/...`) and has a
README with install steps, before/after MD5 checksums and rollback.

## Status

| Change | Tested | Live on a v30.0.01 instance |
|---|---|---|
| Phase 1 + 1.1 | 20-case harness against v30.0.01 classes | Confirmed |
| Phase 2 | 14 end-to-end checks on the v30.0.01 release bundle; control runs on stock v30 | Confirmed |
| AssignHouse hotfix | Reproduced and fixed on the release bundle | Confirmed, with repair |
| Finance (billing the student directly) | Not built: needs agreement upstream | |

## Installing on v30.0.01

Back up each original (e.g. `cp -p file.php file.php.v30bak`), copy the replacement files to
the same paths under your Gibbon root, and check the MD5 checksums in the folder's README.
Install Phase 1 before Phase 2. These files are for **v30.0.01 only**: do not copy them over
a different version.

## Licence

Gibbon is free software under the GNU General Public License v3.0. The files in this
repository are modified Gibbon files and are distributed under the same licence; see
[LICENSE](LICENSE).

Tieku Bortei-Doku, High Point Education Solutions (Official Gibbon Partner)
