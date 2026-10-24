"""End-to-end Phase 2 scenarios against a real local Gibbon v30.0.01 install.
Usage: python3 scenarios.py <label>   (results are read straight from the database)"""
import re, sys, json, glob, os, subprocess
from gibbon_client import Client, alerts

STUDENT_FORM, PARENT_FORM = "000002", "000001"
ADMIN = (os.environ.get("GIBBON_ADMIN_USER", "admin"), os.environ.get("GIBBON_ADMIN_PASS", ""))
DB = os.environ.get("GIBBON_DB", "gib")


def sql(q):
    out = subprocess.run(["mysql", DB, "-N", "-B", "-e", q], capture_output=True, text=True, check=True).stdout
    return [line.split("\t") for line in out.strip().splitlines()] if out.strip() else []


def fill(form, overrides):
    data = dict(form["fields"])
    for name, value in list(data.items()):
        if name in overrides or value not in ("", None):
            continue
        if name in form["selects"]:
            opts = [o for o in form["selects"][name] if o not in ("", "Please select...")]
            data[name] = opts[0] if opts else ""
        elif "dob" in name.lower() or "date" in name.lower():
            data[name] = "01/09/2000"
        elif "email" in name.lower() and name != "emailAddress":
            data[name] = "ref@test.local"
        elif name in ("csrftoken", "nonce", "address", "direction", "emailAddress"):  # emailAddress = honeypot
            pass
        else:
            data[name] = "5550100" if name.startswith("phone") else "Test"
    for name, values in form["radios"].items():
        if name not in data or data[name] in ("", None):
            data[name] = next((v for v in values if v not in ("", None)), "")
    data.update(overrides)
    return data


def apply(email, form_id, overrides, client=None, logged_in=False):
    """Fill in and submit every page of an application. Returns (applicationID, first page HTML)."""
    c = client or Client()
    if logged_in:
        # A logged-in user starts from the select page the same way
        pass
    _, page = c.request("index.php?q=/modules/Admissions/applicationFormSelect.php")
    sel = [f for f in c.forms(page) if "applicationFormSelectProcess" in f["action"]][0]
    url, page = c.request(sel["action"], dict(sel["fields"], gibbonFormID=form_id, admissionsLoginEmail=email))
    first_page = page
    for _ in range(8):
        forms = [f for f in c.forms(page) if "applicationFormProcess" in f["action"]]
        if not forms:
            break
        url, page = c.request(forms[0]["action"], fill(forms[0], overrides))
    app = sql(f"SELECT app.gibbonAdmissionsApplicationID, app.status FROM gibbonAdmissionsApplication app "
              f"JOIN gibbonAdmissionsAccount a ON app.foreignTable='gibbonAdmissionsAccount' AND app.foreignTableID=a.gibbonAdmissionsAccountID "
              f"WHERE a.email='{email}' ORDER BY app.gibbonAdmissionsApplicationID DESC LIMIT 1")
    return (app[0] if app else None), first_page, page


def accept(app_id, inform_student="Y"):
    c = Client()
    c.login(*ADMIN)
    _, page = c.request(f"index.php?q=/modules/Admissions/applications_manage_accept.php&gibbonAdmissionsApplicationID={app_id}&gibbonSchoolYearID=025")
    form = [f for f in c.forms(page) if "acceptProcess" in f["action"]][0]
    checkboxes = sorted(form["radios"].keys())
    data = dict(form["fields"])
    if inform_student == "Y" and "informStudent" in form["radios"]:
        data["informStudent"] = "Y"
    url, result = c.request(form["action"], data)
    return checkboxes, result


def edit_page_alerts(app_id):
    c = Client()
    c.login(*ADMIN)
    _, page = c.request(f"index.php?q=/modules/Admissions/applications_manage_edit.php&gibbonAdmissionsApplicationID={app_id}&gibbonSchoolYearID=025")
    return [a for a in alerts(page) if "This application is attached to an admissions account for" in a]


def account(email):
    r = sql(f"SELECT gibbonAdmissionsAccountID, IFNULL(gibbonPersonID,'NULL'), IFNULL(gibbonFamilyID,'NULL') FROM gibbonAdmissionsAccount WHERE email='{email}'")
    return r[0] if r else None


def result_key(app_id, key):
    r = sql(f"SELECT IFNULL(JSON_UNQUOTE(JSON_EXTRACT(result, '$.{key}')),'NULL'), IFNULL(JSON_UNQUOTE(JSON_EXTRACT(data, '$.{key}')),'NULL') FROM gibbonAdmissionsApplication WHERE gibbonAdmissionsApplicationID={app_id}")
    vals = [v for v in r[0] if v != "NULL"]
    return vals[0] if vals else "NULL"


def person(pid):
    r = sql(f"SELECT CONCAT(preferredName,' ',surname), r.category FROM gibbonPerson p JOIN gibbonRole r ON p.gibbonRoleIDPrimary=r.gibbonRoleID WHERE gibbonPersonID={int(pid)}") if pid not in ("NULL", None, "") else []
    return " / ".join(r[0]) if r else "nobody"


results = []
def check(label, actual, expected):
    ok = actual == expected
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        print(f"         expected: {expected!r}\n         actual:   {actual!r}")


label = sys.argv[1] if len(sys.argv) > 1 else "run"
tag = label.lower()
print(f"=== {label} ===")

student = {"surname": "Mensah", "firstName": "Ama", "preferredName": "Ama", "officialName": "Ama Mensah", "gender": "F",
           "homeAddress": "1 Main St", "homeAddressDistrict": "Accra", "agreement": "on", "payment": "Family"}

# --- Scenario 1: new student applies for themselves -----------------------------------------
print("\n1. New student applies on the student form, and is accepted")
e1 = f"ama.{tag}@test.local"
(app1, status1), first, _ = apply(e1, STUDENT_FORM, dict(student))
email_field = re.search(r'name="email"[^>]*value="([^"]*)"|value="([^"]*)"[^>]*name="email"', first)
prefilled = (email_field.group(1) or email_field.group(2)) if email_field else ""
check("Student email pre-filled from the account email", prefilled, e1)
check("Application submitted (Pending)", status1, "Pending")
boxes, res = accept(app1)
student1 = result_key(app1, "gibbonPersonIDStudent")
check("Accepted, student created", person(student1).endswith("Student"), True)
acc1 = account(e1)
check("Account linked to the student", person(acc1[1]), person(student1))

# --- Scenario 2: the same student applies again from their account ---------------------------
print("\n2. Same account applies again on the student form (second program)")
student2 = dict(student, preferredName="Ama", firstName="Ama")
(app2, status2), first2, _ = apply(e1, STUDENT_FORM, student2)
check("Second application submitted", status2, "Pending")
check("Edit page does NOT call the student 'the parent'", edit_page_alerts(app2), [])
boxes2, res2 = accept(app2)
check("Student NOT recorded as Parent 1 of their own application", person(result_key(app2, "gibbonPersonIDParent1")), "nobody")
check("Account still linked to the student", person(account(e1)[1]), person(student1))

# --- Scenario 3: regression - parent applies for a child on the parent form -------------------
print("\n3. Regression: parent applies for a child on the parent form")
e3 = f"efua.{tag}@test.local"
parent_form = dict(student, firstName="Kwame", preferredName="Kwame", officialName="Kwame Mensah", gender="M",
                   parent1title="Mrs.", parent1surname="Mensah", parent1firstName="Efua", parent1preferredName="Efua",
                   parent1officialName="Efua Mensah", parent1gender="F", parent1relationship="Mother",
                   parent1email=e3, secondParent="No", gibbonFormGroupIDEntry="")
(app3, status3), first3, _ = apply(e3, PARENT_FORM, parent_form)
check("Parent application submitted", status3, "Pending")
boxes3, res3 = accept(app3)
parent3 = result_key(app3, "gibbonPersonIDParent1")
check("Parent 1 created", person(parent3), "Efua Mensah / Parent")
check("Account linked to Parent 1 (unchanged behaviour)", person(account(e3)[1]), "Efua Mensah / Parent")

# --- Scenario 4: regression - the same parent applies for a second child ---------------------
print("\n4. Regression: same parent account applies for a second child")
(app4, status4), _, _ = apply(e3, PARENT_FORM, dict(parent_form, firstName="Akosua", preferredName="Akosua", officialName="Akosua Mensah", gender="F"))
check("Edit page still shows the existing-parent notice", len(edit_page_alerts(app4)), 1)
accept(app4)
check("Existing parent is Parent 1 of the sibling (unchanged behaviour)", person(result_key(app4, "gibbonPersonIDParent1")), "Efua Mensah / Parent")

# --- Scenario 5: accepted adult student applies for their own child on the parent form -------
print("\n5. Accepted adult student applies for their own child on the parent form (agreed design)")
(app5, status5), _, _ = apply(e1, PARENT_FORM, dict(parent_form, firstName="Yaw", preferredName="Yaw", officialName="Yaw Mensah", gender="M", parent1email=e1))
accept(app5)
check("The adult student is Parent 1 on a parent form", person(result_key(app5, "gibbonPersonIDParent1")), person(student1))

passed = sum(results)
print(f"\n{passed} / {len(results)} passed")
