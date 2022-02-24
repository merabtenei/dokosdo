import frappe

def execute():
	frappe.reload_doc("integrations", "doctype", "Social Login Key")

	if frappe.db.exists("Social Login Key", "frappe"):
		frappe.db.set_value("Social Login Key", "frappe", "social_login_provider", "Dodock")
		frappe.db.set_value("Social Login Key", "frappe", "provider_name", "Dodock")
		frappe.rename_doc("Social Login Key", "frappe", "dodock", force=True)