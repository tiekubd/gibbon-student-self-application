"""End-to-end checks for billing the student directly (invoiceTo = Student) on a local Gibbon v30.0.01
with the package and sql/finance_student.sql applied, and the test forms from sql/test_forms.sql.
Reuses the helpers from scenarios.py. Usage: python3 finance_scenarios.py <tag>"""
import os, re, sys, glob, time, email
from email import policy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
head = open(os.path.join(HERE, "scenarios.py")).read().split("results = []")[0]
ns = {"__name__": "helpers"}
exec(compile(head, "scenarios_head", "exec"), ns)
apply, accept, sql, person, result_key, Client, fill = (ns[k] for k in ["apply", "accept", "sql", "person", "result_key", "Client", "fill"])
ADMIN = ns["ADMIN"]

STUDENT_FORM, PARENT_FORM = "000003", "000004"
YEAR = sql("SELECT gibbonSchoolYearID FROM gibbonSchoolYear WHERE status='Current'")[0][0]
FORMGROUP = sql(f"SELECT gibbonFormGroupID FROM gibbonFormGroup WHERE gibbonSchoolYearID={int(YEAR)} ORDER BY name LIMIT 1")[0][0]
MAIL = os.environ.get("GIBBON_MAIL_DIR", "mail")
tag = "fi" + (sys.argv[1] if len(sys.argv) > 1 else "t").lower()
T = re.sub(r"[^a-z]", "", tag).capitalize() or "T"

results = []
def check(label, actual, expected):
    ok = actual == expected
    results.append(ok)
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        print(f"         expected: {expected!r}\n         actual:   {actual!r}")


def enrol_and_accept(app_id):
    """Set the entry form group (staff do this on the application's Office tab) so the student is enrolled, then accept."""
    sql(f"UPDATE gibbonAdmissionsApplication SET data=JSON_SET(data, '$.gibbonFormGroupIDEntry', '{FORMGROUP}') WHERE gibbonAdmissionsApplicationID={int(app_id)}")
    return accept(app_id)


def mails_since(t0, subject_part, marker=None):
    out = []
    for path in sorted(glob.glob(os.path.join(MAIL, "*.eml"))):
        if os.path.getmtime(path) < t0:
            continue
        msg = email.message_from_bytes(open(path, "rb").read(), policy=policy.default)
        if subject_part not in str(msg["Subject"] or ""):
            continue
        body = msg.get_body(preferencelist=("html", "plain"))
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body.get_content() if body else ""))
        if marker and marker not in text:
            continue
        # Finance emails go out as Bcc; the captured envelope keeps them
        rcpt = [a for a in str(msg["Bcc"] or "").split(",") if a.strip()] or [a for a in str(msg["To"] or "").split(",") if a.strip()]
        out.append({"to": sorted(a.strip().lower() for a in rcpt), "text": text})
    return out


def admin():
    c = Client(); c.login(*ADMIN); return c


def invoicee_of(pid):
    r = sql(f"SELECT gibbonFinanceInvoiceeID, invoiceTo, IFNULL(companyName,'NULL'), IFNULL(companyEmail,'NULL') FROM gibbonFinanceInvoicee WHERE gibbonPersonID={int(pid)}")
    return r[0] if r else None


def add_invoice(invoiceeID, amount, name="Tuition"):
    c = admin()
    _, page = c.request(f"index.php?q=/modules/Finance/invoices_manage_add.php&gibbonSchoolYearID={YEAR}")
    f = [f for f in c.forms(page) if "invoices_manage_addProcess" in f["action"]][0]
    data = {"csrftoken": f["fields"]["csrftoken"], "nonce": f["fields"].get("nonce", ""), "address": "/modules/Finance/invoices_manage_add.php",
            "gibbonFinanceInvoiceeIDs[]": [invoiceeID], "scheduling": "Ad Hoc", "invoiceDueDate": "31/12/2026", "notes": "",
            "order[]": ["1"], "name1": name, "gibbonFinanceFeeCategoryID1": "0001", "fee1": str(amount), "feeType1": "Ad Hoc",
            "gibbonFinanceFeeID1": "", "description1": ""}
    c.request(f["action"], data)
    r = sql(f"SELECT gibbonFinanceInvoiceID, invoiceTo, status FROM gibbonFinanceInvoice WHERE gibbonFinanceInvoiceeID={int(invoiceeID)} ORDER BY gibbonFinanceInvoiceID DESC LIMIT 1")
    return r[0] if r else None


def issue_form(invoiceID):
    c = admin()
    _, page = c.request(f"index.php?q=/modules/Finance/invoices_manage_issue.php&gibbonFinanceInvoiceID={invoiceID}&gibbonSchoolYearID={YEAR}")
    f = [f for f in c.forms(page) if "invoices_manage_issueProcess" in f["action"]][0]
    return c, f, page


def recipients(form):
    """Email checkboxes offered on an issue/edit form, and which are ticked."""
    return sorted(v for v in form["radios"].get("emails[]", []) if v), form["fields"].get("emails[]")


def radio_options(page, name):
    """(options, checked) for a radio group. Gibbon prints a radio's value twice; the first is the option's own."""
    found = re.findall(r'<input type="radio" value="([^"]*)"[^>]*name="' + re.escape(name) + r'"[^>]*?(checked)?\s*>', page)
    return [v for v, _ in found], [v for v, ch in found if ch]


def student_email(pid):
    return sql(f"SELECT email FROM gibbonPerson WHERE gibbonPersonID={int(pid)}")[0][0].lower()


base = {"firstName": "Esi", "preferredName": "Esi", "surname": f"Boateng{T}", "officialName": f"Esi Boateng{T}", "gender": "F",
        "homeAddress": "2 Ring Rd", "homeAddressDistrict": "Accra", "agreement": "on", "secondParent": "No",
        "gibbonFormGroupIDEntry": FORMGROUP}
print(f"=== {tag} ===")

# --- Application form ------------------------------------------------------------------------------
print("\nA. Student form offers Myself; parent form doesn't")
es = f"esi.{tag}@test.local"
(app, status), _, last = apply(es, STUDENT_FORM, dict(base, parent1title="Mr.", parent1surname=f"Boateng{T}", parent1firstName="Kojo",
                                                     parent1preferredName="Kojo", parent1officialName=f"Kojo Boateng{T}", parent1gender="M",
                                                     parent1relationship="Father", parent1email=f"kojo.{tag}@test.local"))
c = Client()
# Re-open the student form's last page as a fresh applicant, to read the payment choices
probe = f"probe.{tag}@test.local"
_, page = c.request("index.php?q=/modules/Admissions/applicationFormSelect.php")
sel = [f for f in c.forms(page) if "applicationFormSelectProcess" in f["action"]][0]
_, page = c.request(sel["action"], dict(sel["fields"], gibbonFormID=STUDENT_FORM, admissionsLoginEmail=probe))
seen = None
for _ in range(8):
    forms = [f for f in c.forms(page) if "applicationFormProcess" in f["action"]]
    if not forms: break
    if "payment" in forms[0]["radios"]:
        seen = radio_options(page, "payment"); break
    _, page = c.request(forms[0]["action"], fill(forms[0], base))
check("Student form: Myself, Family, Company", seen[0] if seen else None, ["Student", "Family", "Company"])
check("Student form: Myself selected", seen[1] if seen else None, ["Student"])
check("Myself is the label", bool(re.search(r'value="Student"[^>]*>\s*<label[^>]*>\s*Myself|>\s*Myself\s*<', page)), True)
check("Application submitted with payment = Student", (status, result_key(app, "payment")), ("Pending", "Student"))

c = Client()
_, page = c.request("index.php?q=/modules/Admissions/applicationFormSelect.php")
sel = [f for f in c.forms(page) if "applicationFormSelectProcess" in f["action"]][0]
_, page = c.request(sel["action"], dict(sel["fields"], gibbonFormID=PARENT_FORM, admissionsLoginEmail=f"probe2.{tag}@test.local"))
seenP = None
for _ in range(8):
    forms = [f for f in c.forms(page) if "applicationFormProcess" in f["action"]]
    if not forms: break
    if "payment" in forms[0]["radios"]:
        seenP = radio_options(page, "payment"); break
    _, page = c.request(forms[0]["action"], fill(forms[0], dict(base, parent1email=f"probe2.{tag}@test.local")))
check("Parent form: Family, Company only (unchanged)", seenP, (["Family", "Company"], ["Family"]))

# --- Acceptance --------------------------------------------------------------------------------------
print("\nB. Acceptance creates a Student invoicee")
enrol_and_accept(app)
stu = result_key(app, "gibbonPersonIDStudent")
check("Student created", person(stu), f"Esi Boateng{T} / Student")
check("Student enrolled", bool(sql(f"SELECT 1 FROM gibbonStudentEnrolment WHERE gibbonPersonID={int(stu)} AND gibbonSchoolYearID={int(YEAR)}")), True)
inv = invoicee_of(stu)
check("Invoicee billed to Student, no company details", (inv[1], inv[2] in ("NULL", ""), inv[3] in ("NULL", "")) if inv else None, ("Student", True, True))
semail = student_email(stu)

# --- Invoice ----------------------------------------------------------------------------------------
print("\nC. Invoice billed to the student")
invoice = add_invoice(inv[0], 120)
check("Invoice created as Student, Pending", (invoice[1], invoice[2]) if invoice else None, ("Student", "Pending"))
c, f, page = issue_form(invoice[0])
check("Issue screen: 'Invoice To' shows Student", 'value="Student"' in page, True)
offered, ticked = recipients(f)
check("Issue screen offers the student's email (plus CC self)", semail in offered and f"kojo.{tag}@test.local" not in offered, True)
check("...ticked by default", (ticked or "").lower(), semail)
t0 = time.time() - 1
data = dict(f["fields"]); data["emails[]"] = [semail]
c.request(f["action"], data)
check("Invoice issued", sql(f"SELECT status FROM gibbonFinanceInvoice WHERE gibbonFinanceInvoiceID={int(invoice[0])}")[0][0], "Issued")
m = mails_since(t0, "Invoice", "Tuition")
check("Invoice email sent to the student only", [x["to"] for x in m], [[semail]])
check("Invoice email: 'Invoice To (Student)' with the student's name", bool(m) and "Invoice To (Student)" in m[0]["text"] and f"Esi Boateng{T}" in m[0]["text"], True)
check("...and the family address (student has none of their own)", bool(m) and "2 Ring Rd" in m[0]["text"], True)
check("...not the father", bool(m) and f"Kojo" not in m[0]["text"], True)

print("\nD. Reminder and receipt")
c = admin()
_, page = c.request(f"index.php?q=/modules/Finance/invoices_manage.php&gibbonSchoolYearID={YEAR}&status=Issued")
bulk = [f for f in c.forms(page) if "invoices_manage_processBulk" in f["action"]]
t0 = time.time() - 1
if bulk:
    c.request(bulk[0]["action"], dict(bulk[0]["fields"], action="reminders", **{"gibbonFinanceInvoiceIDs[]": [invoice[0]]}))
m = mails_since(t0, "Reminder")
check("Reminder sent to the student only", [x["to"] for x in m], [[semail]])

_, page = c.request(f"index.php?q=/modules/Finance/invoices_manage_edit.php&gibbonFinanceInvoiceID={invoice[0]}&gibbonSchoolYearID={YEAR}")
ef = [f for f in c.forms(page) if "invoices_manage_editProcess" in f["action"]][0]
offered, ticked = recipients(ef)
check("Payment screen offers the student's email for the receipt", semail in offered, True)
t0 = time.time() - 1
data = dict(ef["fields"], status="Paid", paidAmount="120.00", paidDate="24/10/2026", paymentType="Cash", paymentTransactionID="")
data["emails[]"] = [semail]
c.request(ef["action"], data)
check("Invoice paid", sql(f"SELECT status, paidAmount FROM gibbonFinanceInvoice WHERE gibbonFinanceInvoiceID={int(invoice[0])}")[0], ["Paid", "120.00"])
m = mails_since(t0, "Receipt")
check("Receipt sent to the student", [x["to"] for x in m], [[semail]])
check("Receipt: 'Receipt To (Student)', Paid (Complete), receipt 1", bool(m) and "Receipt To (Student)" in m[0]["text"] and "Paid (Complete)" in m[0]["text"]
      and re.search(r"Receipt Number \(on this invoice\)\s*1\b", m[0]["text"]) is not None, True)

print("\nD2. Bulk issue")
invoice2 = add_invoice(inv[0], 30, "Library")
c = admin()
_, page = c.request(f"index.php?q=/modules/Finance/invoices_manage.php&gibbonSchoolYearID={YEAR}&status=Pending")
bulk = [f for f in c.forms(page) if "invoices_manage_processBulk" in f["action"]]
t0 = time.time() - 1
if bulk:
    c.request(bulk[0]["action"], dict(bulk[0]["fields"], action="issue", **{"gibbonFinanceInvoiceIDs[]": [invoice2[0]]}))
check("Bulk issue: invoice issued", sql(f"SELECT status FROM gibbonFinanceInvoice WHERE gibbonFinanceInvoiceID={int(invoice2[0])}")[0][0], "Issued")
m = mails_since(t0, "Invoice", "Library")
check("Bulk issue: invoice email to the student only", [x["to"] for x in m], [[semail]])
check("Bulk issue: 'Invoice To (Student)'", bool(m) and "Invoice To (Student)" in m[0]["text"], True)

# --- Invoicees ---------------------------------------------------------------------------------------
print("\nE. Manage Invoicees")
_, page = c.request(f"index.php?q=/modules/Finance/invoicees_manage_edit.php&gibbonFinanceInvoiceeID={inv[0]}")
ief = [f for f in c.forms(page) if "invoicees_manage_editProcess" in f["action"]][0]
check("Edit offers Family, Company, Student; Student selected", radio_options(page, "invoiceTo"), (["Family", "Company", "Student"], ["Student"]))
c.request(ief["action"], dict(ief["fields"], invoiceTo="Family"))
check("Switch to Family saved", invoicee_of(stu)[1], "Family")
_, page = c.request(f"index.php?q=/modules/Finance/invoicees_manage_edit.php&gibbonFinanceInvoiceeID={inv[0]}")
ief = [f for f in c.forms(page) if "invoicees_manage_editProcess" in f["action"]][0]
c.request(ief["action"], dict(ief["fields"], invoiceTo="Student"))
check("Switch back to Student saved", invoicee_of(stu)[1], "Student")
_, page = c.request(f"index.php?q=/modules/Finance/invoicees_manage.php&search=Boateng{T}")
check("Invoicees list shows 'Student'", bool(re.search(r"Boateng" + T + r".*?Student", page, re.S)), True)

print("\nE2. Data Updater")
_, page = c.request(f"index.php?q=/modules/Data Updater/data_finance.php&gibbonFinanceInvoiceeID={inv[0]}".replace(" ", "%20"))
check("Finance data update form offers Student, selected", radio_options(page, "invoiceTo"), (["Family", "Company", "Student"], ["Student"]))

print("\nE3. The student sees their own invoices")
# Schools grant Student the existing "View Invoices_mine" permission (Finance > View Invoices)
role = sql("SELECT gibbonRoleID FROM gibbonRole WHERE category='Student' ORDER BY gibbonRoleID LIMIT 1")[0][0]
sql(f"INSERT IGNORE INTO gibbonPermission (gibbonRoleID, gibbonActionID) SELECT {int(role)}, gibbonActionID FROM gibbonAction WHERE name='View Invoices_mine'")
salt = "fiTestSalt0123456789ab"
sql(f"UPDATE gibbonPerson SET passwordStrongSalt='{salt}', passwordStrong=SHA2(CONCAT('{salt}','Student#2026'),256), canLogin='Y', passwordForceReset='N', failCount=0 WHERE gibbonPersonID={int(stu)}")
uname = sql(f"SELECT username FROM gibbonPerson WHERE gibbonPersonID={int(stu)}")[0][0]
sc = Client(); sc.login(uname, "Student#2026")
_, page = sc.request(f"index.php?q=/modules/Finance/invoices_view.php&gibbonSchoolYearID={YEAR}")
check("Student's View Invoices lists their invoices", "120.00" in page and "30.00" in page, True)

# --- Family unchanged ----------------------------------------------------------------------------------
print("\nF. Family invoicee unchanged")
ep = f"ama.{tag}@test.local"
(appP, _), _, _ = apply(ep, PARENT_FORM, dict(base, firstName="Yaa", preferredName="Yaa", officialName=f"Yaa Boateng{T}", payment="Family",
                                               parent1title="Mrs.", parent1surname=f"Boateng{T}", parent1firstName="Ama", parent1preferredName="Ama",
                                               parent1officialName=f"Ama Boateng{T}", parent1gender="F", parent1relationship="Mother", parent1email=ep))
enrol_and_accept(appP)
stuP = result_key(appP, "gibbonPersonIDStudent")
invP = invoicee_of(stuP)
check("Parent-form invoicee is Family", invP[1] if invP else None, "Family")
invoiceP = add_invoice(invP[0], 80)
check("Invoice created as Family", invoiceP[1] if invoiceP else None, "Family")
c, f, page = issue_form(invoiceP[0])
offered, _ = recipients(f)
check("Issue screen offers the parent, not the student", ep in offered and student_email(stuP) not in offered, True)

print(f"\n{sum(results)} / {len(results)} passed")
