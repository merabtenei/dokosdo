import frappe
import json

def execute():
	users = frappe.get_all("User", dict(user_type="System User"))
	version = frappe.utils.change_log.get_versions()
	version["frappe"]["version"] = '1.1.0'

	for user in users:
		frappe.db.set_value("User", user.name, "last_known_versions", \
			json.dumps(version), update_modified=False)
