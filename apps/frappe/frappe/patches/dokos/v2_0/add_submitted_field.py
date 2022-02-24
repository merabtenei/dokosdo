import frappe
from frappe.modules.import_file import get_file_path, read_doc_from_file

def execute():
	doctypes = frappe.get_all("DocType", filters={"istable": 0, "issingle": 0, "is_submittable": 1}, fields=["module", "name"])

	for doctype in doctypes:
		try:
			path = get_file_path(doctype.module, "doctype", doctype.name)
			try:
				read_doc_from_file(path)
			except IOError:
				continue

			frappe.reload_doc(doctype.module, "doctype", doctype.name, force=True)
		except Exception:
			pass