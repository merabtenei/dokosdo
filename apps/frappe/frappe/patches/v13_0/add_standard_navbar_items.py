from __future__ import unicode_literals
import frappe
from frappe.utils.install import add_standard_navbar_items

def execute():
	# Add standard navbar items for ERPNext in Navbar Settings
	frappe.reload_doc('core', 'doctype', 'navbar_settings')
	frappe.reload_doc('core', 'doctype', 'navbar_item')
	add_standard_navbar_items()

	meta = frappe.get_meta("System Settings")
	if meta.has_field("desk_logo"):
		desk_logo = frappe.db.get_single_value("System Settings", "desk_logo")
		if desk_logo:
			frappe.db.set_value('Navbar Settings', 'Navbar Settings', 'app_logo', desk_logo)