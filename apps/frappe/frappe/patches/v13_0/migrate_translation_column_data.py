import frappe
from frappe.model.utils.rename_field import rename_field
from frappe.model.meta import get_table_columns

def execute():
	frappe.reload_doc('core', 'doctype', 'Translation')
	
	if "source_name" in get_table_columns("Translation"):
		rename_field("Translation", "source_name", "source_text")

	if "target_name" in get_table_columns("Translation"):
		rename_field("Translation", "target_name", "translated_text")

	frappe.db.commit()