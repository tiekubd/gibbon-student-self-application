"""Run the Gibbon v30 web installer non-interactively (local throwaway test site only)."""
import os, sys, re
from gibbon_client import Client
c = Client()
def last_nonce(page, fields):
    n = re.findall(r'name="nonce"[^>]*value="([^"]*)"|value="([^"]*)"[^>]*name="nonce"', page)
    if n: fields["nonce"] = [a or b for a, b in n][-1]
    return fields
_, page = c.request("installer/install.php")
f = [f for f in c.forms(page) if "install.php" in f["action"]][-1]
_, page = c.request(f["action"] if f["action"].startswith("http") else "installer/" + f["action"].lstrip("./"), last_nonce(page, dict(f["fields"], code="en_GB")))
f = [f for f in c.forms(page) if "install.php" in f["action"]][-1]
_, page = c.request("installer/" + f["action"].lstrip("./"), last_nonce(page, dict(f["fields"], databaseServer="localhost", databaseName=os.environ["GIBBON_DB"],
    databaseUsername=os.environ["GIBBON_DB_USER"], databasePassword=os.environ["GIBBON_DB_PASS"], demoData="Y")))
f = [f for f in c.forms(page) if "install.php" in f["action"]][-1]
fields = dict(f["fields"], title="Mr.", surname="Admin", firstName="Test", email="admin@test.local", username="admin",
    passwordNew=os.environ["GIBBON_ADMIN_PASS"], passwordConfirm=os.environ["GIBBON_ADMIN_PASS"], absoluteURL=os.environ["GIBBON_URL"], absolutePath=sys.argv[1],
    systemName="Gibbon", organisationName="Test School", organisationNameShort="TS", currency="USD $", country="Ghana", timezone="Africa/Accra")
fields.pop("support", None)
last_nonce(page, fields)
_, page = c.request("installer/" + f["action"].lstrip("./"), fields)
print("installed" if "Congratulations" in page or "successful" in page.lower() else page[-3000:])
