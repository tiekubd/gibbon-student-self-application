import sys
src = open("scenarios.py").read().split("results = []")[0]
ns = {}; exec(compile(src, "s", "exec"), ns)
tag = sys.argv[1]
student = {"surname": "Osei", "firstName": "Kojo", "preferredName": "Kojo", "officialName": "Kojo Osei", "gender": "M",
           "homeAddress": "1 Main St", "homeAddressDistrict": "Accra", "agreement": "on", "payment": "Family"}
(app, status), _, _ = ns["apply"](f"kojo.{tag}@test.local", "000002", student)
ns["accept"](app)
sid = ns["result_key"](app, "gibbonPersonIDStudent")
print(tag, "| result house:", ns["result_key"](app, "gibbonHouseID"),
      "| student house:", ns["sql"](f"SELECT IFNULL(gibbonHouseID,'NULL') FROM gibbonPerson WHERE gibbonPersonID={int(sid)}")[0][0],
      "| person 1 house:", ns["sql"]("SELECT IFNULL(gibbonHouseID,'NULL') FROM gibbonPerson WHERE gibbonPersonID=1")[0][0])
