import frappe

def execute():
	folder_name = frappe.db.get_value("File", {"is_attachments_folder": 1})
	if folder_name:
		frappe.db.sql('''
			UPDATE tabFile
			SET folder = %s
			WHERE ifnull(attached_to_doctype, '') != ''
			AND folder = 'Home'
		''', folder_name)