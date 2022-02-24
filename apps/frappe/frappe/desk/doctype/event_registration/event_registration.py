# -*- coding: utf-8 -*-
# Copyright (c) 2020, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import _

class EventRegistration(Document):
	def validate(self):
		self.check_duplicates()
		self.create_or_link_with_contact()

	def on_submit(self):
		self.add_contact_to_event()

	def on_cancel(self):
		self.remove_contact_from_event()

	def check_duplicates(self):
		if frappe.db.exists("Event Registration", dict(email=self.email, event=self.event, name=("!=", self.name), docstatus=1)):
			frappe.throw(_("User is already registered for this event."))

	def create_or_link_with_contact(self):
		contact = self.contact
		if not contact:
			contact = frappe.db.get_value("Contact", dict(email_id=self.email))

		if not contact and self.user:
			contact = frappe.db.get_value("Contact", dict(user=self.user))

		if not contact:
			contact = frappe.get_doc({
				"first_name": self.first_name,
				"last_name": self.last_name,
				"user": self.user
			})
			contact.add_email(self.email, is_primary=1)
			contact.insert(ignore_permissions=True)

		self.contact = contact

	def add_contact_to_event(self):
		event = frappe.get_doc("Event", self.event)
		event.add_participant(self.contact)
		event.save(ignore_permissions=True)

	def remove_contact_from_event(self):
		event = frappe.get_doc("Event", self.event)
		event.remove_participant(self.contact)
		event.save(ignore_permissions=True)

@frappe.whitelist()
def get_user_info(user=None):
	if not user:
		user = frappe.session.user

	return frappe.db.get_value("User", user, ["first_name", "last_name", "email", "mobile_no"], as_dict=True)


@frappe.whitelist(allow_guest=True)
def register_to_event(event, data, user=None):
	try:
		registration = frappe.get_doc(
			dict({ 
				"doctype": "Event Registration",
				"event": event,
				"user": user or frappe.session.user
			}, **frappe.parse_json(data))
		)

		registration.insert(ignore_permissions=True, ignore_mandatory=True)
		registration.submit()
		return registration
	except Exception:
		return

@frappe.whitelist()
def cancel_registration(event, user=None):
	if not user:
		user = frappe.session.user

	registration = frappe.get_value("Event Registration", dict(user=user, event=event, docstatus=1))

	if registration:
		doc = frappe.get_doc("Event Registration", registration)
		doc.flags.ignore_permissions=True
		doc.cancel()

	return registration