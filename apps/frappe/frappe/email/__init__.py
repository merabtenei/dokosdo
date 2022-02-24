# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.desk.reportview import build_match_conditions
import re

def sendmail_to_system_managers(subject, content):
	frappe.sendmail(recipients=get_system_managers(), subject=subject, content=content)

@frappe.whitelist()
def get_contact_list(txt, page_length=20):
	"""Returns contacts (from autosuggest)"""

	cached_contacts = get_cached_contacts(txt)
	if cached_contacts:
		return cached_contacts[:page_length]

	try:
		match_conditions = build_match_conditions('Contact')
		match_conditions = "and {0}".format(match_conditions) if match_conditions else ""

		out = frappe.db.sql("""select email_id as value,
			concat(first_name, ifnull(concat(' ',last_name), '' )) as description
			from tabContact
			where name like %(txt)s or email_id like %(txt)s
			%(condition)s
			limit %(page_length)s""", {
				'txt': '%' + txt + '%',
				'condition': match_conditions,
				'page_length': page_length
			}, as_dict=True)
		out = filter(None, out)

	except:
		raise

	update_contact_cache(out)

	return out

def get_system_managers():
	return frappe.db.sql_list("""select parent FROM `tabHas Role`
		WHERE role='System Manager'
		AND parent!='Administrator'
		AND parent IN (SELECT email FROM tabUser WHERE enabled=1)""")

@frappe.whitelist()
def relink(name, reference_doctype=None, reference_name=None):
	frappe.db.sql("""update
			`tabCommunication`
		set
			reference_doctype = %s,
			reference_name = %s,
			status = "Linked"
		where
			communication_type = "Communication" and
			name = %s""", (reference_doctype, reference_name, name))

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_communication_doctype(doctype, txt, searchfield, start, page_len, filters):
	from frappe.modules import load_doctype_module
	com_doctypes = []
	if len(txt)<2:

		for name in frappe.get_hooks("communication_doctypes"):
			try:
				module = load_doctype_module(name, suffix='_dashboard')
				if hasattr(module, 'get_data'):
					for i in module.get_data()['transactions']:
						com_doctypes += i["items"]
			except ImportError:
				pass
	else:
		com_doctypes = [d[0] for d in frappe.db.get_values("DocType", {"issingle": 0, "istable": 0, "hide_toolbar": 0})]

	filtered_doctypes = tuple([v for v in com_doctypes if re.search(txt+".*", _(v), re.IGNORECASE)])
	allowed_doctypes = frappe.permissions.get_doctypes_with_read()

	valid_doctypes = sorted(set(filtered_doctypes).intersection(set(allowed_doctypes)))
	valid_doctypes = [[doctype] for doctype in valid_doctypes]

	return valid_doctypes

def get_cached_contacts(txt):
	contacts = frappe.cache().hget("contacts", frappe.session.user) or []

	if not contacts:
		return

	if not txt:
		return contacts

	match = [d for d in contacts if (d.value and ((d.value and txt.lower() in d.value.lower()) or (d.description and txt.lower() in d.description.lower())))]
	return match

def update_contact_cache(contacts):
	cached_contacts = frappe.cache().hget("contacts", frappe.session.user) or []

	uncached_contacts = [d for d in contacts if d not in cached_contacts]
	cached_contacts.extend(uncached_contacts)

	frappe.cache().hset("contacts", frappe.session.user, cached_contacts)
