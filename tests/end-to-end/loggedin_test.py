"""Usage: loggedin_test.py <username> <formID> <tag>. Needs GIBBON_STUDENT_PASS (that student's password)
and the Student role granted Admissions > My Application Forms.
An accepted student logs in, applies again on the student form, and is accepted. Reports what each page shows and the result."""
import sys, os, re, time
src = open(os.path.join(os.path.dirname(__file__), "scenarios.py")).read().split("results = []")[0]
ns = {}; exec(compile(src, "s", "exec"), ns)
c = ns["Client"](); sql = ns["sql"]
username, form_id, tag = sys.argv[1], sys.argv[2], sys.argv[3]
official = f"Kwesi Again{tag.capitalize()}"
c.login(username, os.environ["GIBBON_STUDENT_PASS"])
_, page = c.request("index.php?q=/modules/Admissions/applicationFormView.php")
setup = [f for f in c.forms(page) if "applicationFormViewProcess" in f["action"]]
if setup:  # first visit: Gibbon creates the admissions account for this logged-in user
    c.request(setup[0]["action"], ns["fill"](setup[0], {}))
    _, page = c.request("index.php?q=/modules/Admissions/applicationFormView.php")
print("My Application Forms page:", "New Application Form" in page, "| errors:", [a[:90] for a in ns["alerts"](page) if "access" in a.lower()][:2])
start = [f for f in c.forms(page) if f["action"].endswith("applicationForm.php")][0]
url, page = c.request(start["action"], dict(start["fields"], gibbonFormID=form_id))
def val(page, name):
    m = re.search(r'<(?:input|select|textarea)[^>]*\bname="%s"[^>]*>' % re.escape(name), page)
    if not m: return None
    v = re.search(r'value="([^"]*)"', m.group(0)); return v.group(1) if v else ""
over = {"surname": f"Again{tag.capitalize()}", "firstName": "Kwesi", "preferredName": "Kwesi", "officialName": official, "gender": "M", "agreement": "on",
        "parent1title": "Mrs.", "parent1surname": "Mensah", "parent1firstName": "Abena", "parent1preferredName": "Abena",
        "parent1officialName": "Abena Mensah", "parent1gender": "F", "parent1relationship": "Mother", "parent1email": f"abena.{username}@test.local",
        "secondParent": "No"}
for p in range(1, 7):
    if "Uncaught" in page or "TypeError" in page or (len(page) < 2000):
        print(f"page {p}: PAGE ERROR (length {len(page)})"); break
    att = [a[:90] for a in ns["alerts"](page) if "attached to an admissions account" in a]
    fams = re.findall(r'<input[^>]*name="gibbonFamilyID"[^>]*>', page)
    hidden_p1 = re.search(r'<input[^>]*type="hidden"[^>]*name="gibbonPersonIDParent1"[^>]*value="([^"]*)"', page)
    info = {"parent1surname field": val(page, "parent1surname"), "family choices": len(fams), "hidden Parent1 id": hidden_p1.group(1) if hidden_p1 else None, "attached notice": att}
    print(f"page {p}:", {k: v for k, v in info.items() if v not in (None, [], 0)}, [x[:100] for x in ns["alerts"](page) if "required" in x.lower() or "error" in x.lower()][:1])
    if p == 3:
        f3 = [x for x in c.forms(page) if "applicationFormProcess" in x["action"]][0]
        print("   family radio:", f3["radios"].get("gibbonFamilyID"), "| filled:", ns["fill"](f3, over).get("gibbonFamilyID"))
    forms = [x for x in c.forms(page) if "applicationFormProcess" in x["action"]]
    if not forms: break
    url, page = c.request(forms[0]["action"], ns["fill"](forms[0], over))
app = sql(f"SELECT gibbonAdmissionsApplicationID, status FROM gibbonAdmissionsApplication WHERE JSON_UNQUOTE(JSON_EXTRACT(data,'$.officialName'))='{official}' ORDER BY 1 DESC LIMIT 1")
print("application:", app)
if app and app[0][1] == "Pending":
    ns["accept"](app[0][0])
    p1 = ns["result_key"](app[0][0], "gibbonPersonIDParent1"); st = ns["result_key"](app[0][0], "gibbonPersonIDStudent")
    print("Parent 1 after acceptance:", ns["person"](p1)); print("Student created:", ns["person"](st))
    me = sql(f"SELECT gibbonPersonID FROM gibbonPerson WHERE username='{username}'")[0][0]
    acc = sql(f"SELECT IFNULL(gibbonPersonID,'NULL') FROM gibbonAdmissionsAccount WHERE gibbonPersonID={int(me)}")
    print("Account still linked to the logged-in student:", bool(acc))
