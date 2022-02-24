import frappe

def execute():
	frappe.reload_doc("desk", "doctype", "Workspace Shortcut")
	for shortcut in frappe.get_all("Workspace Shortcut", filters={"color": "Grey"}):
		frappe.db.set_value("Workspace Shortcut", shortcut.name, "color", "Gray")