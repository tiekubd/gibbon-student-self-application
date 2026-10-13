"""Accept a student-form application with both 'inform' boxes ticked; list who each welcome email went to."""
import sys, os, glob, time, email, re
from email import policy
src = open(os.path.join(os.path.dirname(__file__), "scenarios.py")).read().split("results = []")[0]
ns = {}; exec(compile(src, "s", "exec"), ns)
tag = sys.argv[1]; start = time.time()
stu = {"surname": f"Welcome{tag.capitalize()}", "firstName": "Kwesi", "preferredName": "Kwesi", "officialName": "Kwesi W", "gender": "M",
       "homeAddress": "1 Main St", "homeAddressDistrict": "Accra", "agreement": "on", "payment": "Family", "secondParent": "No",
       "parent1title": "Mrs.", "parent1surname": f"Welcome{tag.capitalize()}", "parent1firstName": "Abena", "parent1preferredName": "Abena",
       "parent1officialName": "Abena W", "parent1gender": "F", "parent1relationship": "Mother", "parent1email": f"abena.{tag}@test.local"}
(app, status), _, _ = ns["apply"](f"kwesi.{tag}@test.local", "000003", stu)
# accept with both boxes ticked, as in the screenshot
c = ns["Client"](); c.login(*ns["ADMIN"])
_, page = c.request(f"index.php?q=/modules/Admissions/applications_manage_accept.php&gibbonAdmissionsApplicationID={app}&gibbonSchoolYearID=025")
form = [f for f in c.forms(page) if "acceptProcess" in f["action"]][0]
c.request(form["action"], dict(form["fields"], informStudent="Y", informParents="Y"))
time.sleep(1)
for p in sorted(glob.glob(os.path.join(os.environ.get("GIBBON_MAIL_DIR", "mail"), "*.eml"))):
    if os.path.getmtime(p) < start - 1: continue
    m = email.message_from_bytes(open(p, "rb").read(), policy=policy.default)
    if "Welcome" not in str(m["Subject"]): continue
    body = m.get_body(preferencelist=("html", "plain")).get_content()
    dear = re.search(r"Dear\s*([^,<]*),", re.sub(r"<[^>]+>", " ", body))
    user = re.search(r"Username:\s*([^\s<]+)", re.sub(r"<[^>]+>", " ", body))
    print(f"Dear {dear.group(1).strip() if dear else '?'} | username {user.group(1) if user else '?'} | To: {m['To']}")
