"""End-to-end checks for the applicant-type build on a local Gibbon v30.0.01.
Reuses the helpers from scenarios.py (apply, accept, sql, person, ...).
Usage: python3 applicant_scenarios.py <tag>"""
import os, re, sys, glob, time, email
from email import policy

HERE = os.path.dirname(os.path.abspath(__file__))
SCEN = os.path.join(HERE, "scenarios.py")
sys.path.insert(0, HERE)
head = open(SCEN).read().split("results = []")[0]
ns = {"__name__": "helpers"}
exec(compile(head, "scenarios_head", "exec"), ns)
apply, accept, sql, person, account, result_key, edit_page_alerts, alerts = (
    ns[k] for k in ["apply", "accept", "sql", "person", "account", "result_key", "edit_page_alerts", "alerts"])
Client = ns["Client"]

UNI, PARENTFORM = "000003", "000004"   # the pair: "Application by a student" / "by a parent or guardian"
# "ap" keeps this suite's test addresses apart from scenarios.py run with the same tag
tag = "ap" + (sys.argv[1] if len(sys.argv) > 1 else "t").lower()
T = re.sub(r"[^a-z]", "", tag).capitalize() or "T"
start = time.time()

results = []
def check(label, actual, expected):
    ok = actual == expected
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        print(f"         expected: {expected!r}\n         actual:   {actual!r}")


def confirmation_emails(marker):
    """Captured 'Application Form Confirmation' emails mentioning marker, sent during this run."""
    out = []
    for path in sorted(glob.glob(os.path.join(os.environ.get("GIBBON_MAIL_DIR", "mail"), "*.eml"))):
        if os.path.getmtime(path) < start - 1:
            continue
        msg = email.message_from_bytes(open(path, "rb").read(), policy=policy.default)
        if "Confirmation" not in str(msg["Subject"] or ""):
            continue
        body = msg.get_body(preferencelist=("html", "plain"))
        text = body.get_content() if body else ""
        if marker not in text:
            continue
        to = sorted(a.strip().lower() for a in str(msg["To"] or "").split(","))
        greet = re.search(r"Dear\s*([^,<]*),", re.sub(r"<[^>]+>", " ", text))
        out.append({"to": to, "dear": re.sub(r"\s+", " ", greet.group(1)).strip() if greet else None})
    return out


def form_select_page():
    _, page = Client().request("index.php?q=/modules/Admissions/applicationFormSelect.php")
    return page


def admin_edit_page(app_id):
    c = Client(); c.login(*ns["ADMIN"])
    _, page = c.request(f"index.php?q=/modules/Admissions/applications_manage_edit.php&gibbonAdmissionsApplicationID={app_id}&gibbonSchoolYearID=025")
    return page


student = {"firstName": "Kwesi", "preferredName": "Kwesi", "surname": f"Asante{T}", "officialName": f"Kwesi Asante{T}",
           "gender": "M", "homeAddress": "1 Main St", "homeAddressDistrict": "Accra", "agreement": "on", "payment": "Family",
           "secondParent": "No", "gibbonFormGroupIDEntry": ""}
with_parent = dict(student, parent1title="Mrs.", parent1surname=f"Asante{T}", parent1firstName="Abena", parent1preferredName="Abena",
                   parent1officialName=f"Abena Asante{T}", parent1gender="F", parent1relationship="Mother")

print(f"=== {tag} ===")

# --- University form: student applies, parent details collected -------------------------------
print("\nU. Application by a student (setting: the student, for themselves), parent details filled in")
eu, mother = f"kwesi.{tag}@test.local", f"abena.{tag}@test.local"
(app, status), first, _ = apply(eu, UNI, dict(with_parent, parent1email=mother))
m = re.search(r'<input[^>]*\bname="email"[^>]*>', first)
check("Student email pre-filled from the account email, despite parent fields", bool(m) and f'value="{eu}"' in m.group(0), True)
check("Application submitted", status, "Pending")
mails = confirmation_emails(f"Asante{T}")
check("One confirmation email", len(mails), 1)
if mails:
    check("Confirmation goes to the student, not the parent", mails[0]["to"], [eu])
    check("Confirmation greets the student", mails[0]["dear"], f"Kwesi Asante{T}")
accept(app)
stu = result_key(app, "gibbonPersonIDStudent")
par = result_key(app, "gibbonPersonIDParent1")
check("Student created", person(stu), f"Kwesi Asante{T} / Student")
check("Parent still created from the parent fields", person(par), f"Abena Asante{T} / Parent")
check("Family created", result_key(app, "familyCreated") in ("true", "1"), True)
check("Admissions account linked to the STUDENT, not the parent", person(account(eu)[1]), f"Kwesi Asante{T} / Student")

print("\nU2. Same student applies again on the student form")
(app2, status2), _, _ = apply(eu, UNI, dict(with_parent, parent1email=mother, firstName="Kwesi"))
page = admin_edit_page(app2)
check("Edit page: no 'attached to an admissions account' parent notice", [a for a in alerts(page) if "This application is attached to an admissions account for" in a], [])
check("Edit page: Parent 1 fields still editable (not replaced by the student)", 'name="parent1surname"' in page, True)
accept(app2)
p2 = result_key(app2, "gibbonPersonIDParent1")
check("The student is NOT Parent 1 of their own second application", person(p2) != person(stu), True)
check("Parent 1 is the parent from the form", person(p2), f"Abena Asante{T} / Parent")
check("Account still linked to the student", person(account(eu)[1]), f"Kwesi Asante{T} / Student")

# --- The parent form of the pair ---------------------------------------------------------------
print("\nP. Application by a parent or guardian (setting saved as: a parent or guardian, for a student)")
sel = form_select_page()
check("Applicants see both forms by name", "Application by a student" in sel and "Application by a parent or guardian" in sel, True)
check("...with their descriptions", "For students applying for themselves." in sel and "For parents or guardians applying for a student." in sel, True)
ep = f"ama.{tag}@test.local"
(appP, sP), firstP, _ = apply(ep, PARENTFORM, dict(with_parent, firstName="Yaw", preferredName="Yaw", officialName=f"Yaw Asante{T}",
                                                   parent1firstName="Ama", parent1preferredName="Ama", parent1officialName=f"Ama Asante{T}", parent1email=ep))
email_input = re.search(r'<input[^>]*\bname="email"[^>]*>', firstP)
check("Student email field is on page 1", bool(email_input), True)
check("Student email NOT pre-filled with the parent's account email", bool(email_input) and f'value="{ep}"' in email_input.group(0), False)
mails = confirmation_emails("Yaw")
check("Confirmation goes to the parent", mails[-1]["to"] if mails else None, [ep])
check("Confirmation greets the parent", mails[-1]["dear"] if mails else None, f"Mrs. Ama Asante{T}")
accept(appP)
check("Account linked to Parent 1", person(account(ep)[1]), f"Ama Asante{T} / Parent")

print("\nP2. Same parent applies for a second child")
(appP2, _), _, _ = apply(ep, PARENTFORM, dict(student, firstName="Efua", preferredName="Efua", officialName=f"Efua Asante{T}", gender="F"))
accept(appP2)
check("Parent 1 is the existing parent (Gibbon's existing behaviour)", person(result_key(appP2, "gibbonPersonIDParent1")), f"Ama Asante{T} / Parent")
check("Second child created", person(result_key(appP2, "gibbonPersonIDStudent")), f"Efua Asante{T} / Student")

print("\nX. The accepted student from U uses their own account on the parent form (e.g. for their own child)")
(appX, _), _, _ = apply(eu, PARENTFORM, dict(student, firstName="Kofi", preferredName="Kofi", officialName=f"Kofi Asante{T}"))
accept(appX)
check("On a parent form, the account holder is Parent 1", person(result_key(appX, "gibbonPersonIDParent1")), f"Kwesi Asante{T} / Student")

# --- Form Builder setting ------------------------------------------------------------------------
print("\nF. Form Builder setting")
c = Client(); c.login(*ns["ADMIN"])
_, page = c.request(f"index.php?q=/modules/System Admin/formBuilder_edit.php&gibbonFormID={UNI}".replace(" ", "%20"))
cfg = [f for f in c.forms(page) if "formBuilder_editConfigProcess" in f["action"]]
check("Active Features shows 'Who completes this application?'", bool(cfg) and "applicantType" in cfg[0]["selects"], True)
if cfg:
    check("Two choices, parent first", cfg[0]["selects"]["applicantType"], ["Parent", "Student"])
    _, sp = c.request("index.php?q=/modules/System Admin/formBuilder_edit.php&gibbonFormID=000001")
    sf = [f for f in c.forms(sp) if "formBuilder_editConfigProcess" in f["action"]]
    check("Sample Application Form (never set) shows the parent choice", sf[0]["fields"].get("applicantType") if sf else None, "Parent")
    check("Current value shown", cfg[0]["fields"].get("applicantType"), "Student")
    action = cfg[0]["action"].replace(" ", "%20")
    def save(**changes):
        _, pg = c.request(f"index.php?q=/modules/System Admin/formBuilder_edit.php&gibbonFormID={UNI}")
        f = [f for f in c.forms(pg) if "formBuilder_editConfigProcess" in f["action"]][0]
        c.request(action, dict(f["fields"], **changes))
    def saved():
        return sql(f"SELECT JSON_UNQUOTE(JSON_EXTRACT(config,'$.applicantType')) FROM gibbonForm WHERE gibbonFormID={int(UNI)}")[0][0]
    other = lambda k: sql(f"SELECT JSON_UNQUOTE(JSON_EXTRACT(config,'$.{k}')) FROM gibbonForm WHERE gibbonFormID={int(UNI)}")[0][0]
    before_other = other("createFamily")
    save()
    check("Saving Active Features keeps the setting", saved(), "Student")
    save(applicantType="Parent")
    check("Changing the setting is saved", saved(), "Parent")
    save(applicantType="Student")
    check("Other Active Features settings untouched", other("createFamily"), before_other)
    check("Setting restored", saved(), "Student")

print(f"\n{sum(results)} / {len(results)} passed")
