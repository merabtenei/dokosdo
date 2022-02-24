# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import validate_email_address
from frappe.model.document import Document
from frappe.utils import parse_addr

class EmailGroup(Document):
	def onload(self):
			singles = [d.name for d in frappe.db.get_all("DocType", "name", {"issingle": 1})]
			import_types = [{"value": d.parent, "label": "{0} ({1})".format(_(d.parent), _(d.label))} \
				for d in frappe.db.get_all("DocField", ("parent", "label"), {"options": "Email"})
				if d.parent not in singles]
			import_types.sort(key=lambda x:x["label"])
			self.get("__onload").import_types = import_types

	def import_from(self, doctype, filters=None, auto_update=False):
		"""Extract Email Addresses from given doctype and add them to the current list"""
		self.import_doctype = doctype
		self.import_filters = filters or "{}"
		self.auto_update = auto_update

		added = self.import_data()

		frappe.msgprint(_("{0} subscribers added").format(added))

		return self.update_total_subscribers()

	def import_data(self):
		meta = frappe.get_meta(self.import_doctype)
		email_field = [d.fieldname for d in meta.fields if d.fieldtype in ("Data", "Small Text", "Text", "Code", "Read Only") and d.options=="Email"][0]
		unsubscribed_field = "unsubscribed" if meta.get_field("unsubscribed") else None
		added = 0

		frappe.flags.mute_messages = True
		for user in frappe.db.get_all(self.import_doctype, filters=frappe.parse_json(self.import_filters), fields=[email_field, unsubscribed_field or "name"], limit=999999):
			try:
				email = parse_addr(user.get(email_field))[1] if user.get(email_field) else None
				if email:
					frappe.get_doc({
						"doctype": "Email Group Member",
						"email_group": self.name,
						"email": email,
						"unsubscribed": user.get(unsubscribed_field) if unsubscribed_field else 0
					}).insert(ignore_permissions=True)

					added += 1
			except frappe.UniqueValidationError:
				continue
		frappe.flags.mute_messages = False

		return added

	def update_total_subscribers(self):
		self.total_subscribers = self.get_total_subscribers()
		self.db_update()
		return self.total_subscribers

	def get_total_subscribers(self):
		return frappe.db.sql("""select count(*) from `tabEmail Group Member`
			where email_group=%s""", self.name)[0][0]

	def on_trash(self):
		for d in frappe.get_all("Email Group Member", "name", {"email_group": self.name}):
			frappe.delete_doc("Email Group Member", d.name)

@frappe.whitelist()
def import_from(name, doctype, filters=None, auto_update=False):
	nlist = frappe.get_doc("Email Group", name)
	if nlist.has_permission("write"):
		return nlist.import_from(doctype, filters, auto_update)

@frappe.whitelist()
def add_subscribers(name, email_list):
	if not isinstance(email_list, (list, tuple)):
		email_list = email_list.replace(",", "\n").split("\n")

	template = frappe.db.get_value('Email Group', name, 'welcome_email_template')
	welcome_email = frappe.get_doc("Email Template", template) if template else None

	count = 0
	for email in email_list:
		email = email.strip()
		parsed_email = validate_email_address(email, False)

		if parsed_email:
			if not frappe.db.get_value("Email Group Member",
				{"email_group": name, "email": parsed_email}):
				frappe.get_doc({
					"doctype": "Email Group Member",
					"email_group": name,
					"email": parsed_email
				}).insert(ignore_permissions=frappe.flags.ignore_permissions)

				send_welcome_email(welcome_email, parsed_email, name)

				count += 1
			else:
				pass
		else:
			frappe.msgprint(_("{0} is not a valid Email Address").format(email))

	frappe.msgprint(_("{0} subscribers added").format(count))

	return frappe.get_doc("Email Group", name).update_total_subscribers()

def send_welcome_email(welcome_email, email, email_group):
	"""Send welcome email for the subscribers of a given email group."""
	if not welcome_email:
		return

	args = dict(
		email=email,
		email_group=email_group
	)

	message = frappe.render_template(welcome_email.response, args)
	frappe.sendmail(email, subject=welcome_email.subject, message=message)

def auto_update_email_groups():
	email_groups = frappe.get_all("Email Group", filters={"auto_update": 1}, pluck="name")
	for email_group in email_groups:
		doc = frappe.get_doc("Email Group", email_group)
		doc.import_data()
		doc.update_total_subscribers()