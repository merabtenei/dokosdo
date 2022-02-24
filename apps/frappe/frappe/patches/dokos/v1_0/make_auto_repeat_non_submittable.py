import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
	frappe.reload_doc("automation", "doctype", "auto_repeat")

	auto_repeats = frappe.get_all("Auto Repeat",\
		fields=["name", "docstatus", "status", "reference_doctype"])
	references = set()
	for auto_repeat in auto_repeats:
		if auto_repeat["docstatus"] == 2 or auto_repeat["status"] in ["Stopped", "Cancelled"]:
			frappe.db.set_value("Auto Repeat", auto_repeat["name"], "disabled", 1)

		if auto_repeat["docstatus"] != 0:
			frappe.db.set_value("Auto Repeat", auto_repeat["name"], "docstatus", 0)

		references.add(auto_repeat["reference_doctype"])

	for reference in references:
		frappe.make_property_setter({
			"doctype": reference,
			"doctype_or_field": "DocType",
			"property": "allow_auto_repeat",
			"value": 1,
			"property_type": "Check"
		})
		if not frappe.db.exists('Custom Field', {'fieldname': 'auto_repeat', 'dt': reference}):
			doc = frappe.get_doc("DocType", reference)
			insert_after = doc.fields[len(doc.fields) - 1].fieldname
			df = dict(fieldname='auto_repeat', label='Auto Repeat', fieldtype='Link', options='Auto Repeat',\
				insert_after=insert_after, read_only=1, no_copy=1, print_hide=1)
			create_custom_field(reference, df)

	for auto_repeat in auto_repeats:
		doc = frappe.get_doc("Auto Repeat", auto_repeat["name"])
		doc.update_status()
		try:
			doc.save()
		except frappe.ValidationError:
			continue