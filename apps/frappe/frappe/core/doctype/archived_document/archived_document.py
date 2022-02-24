# -*- coding: utf-8 -*-
# Copyright (c) 2021, Dokos SAS and contributors
# For license information, please see license.txt
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.utils.seal import get_sealed_doc, get_chained_seal

exclude_from_linked_with = True

class ArchivedDocument(Document):
	def before_insert(self):
		sealed_doc = self.data
		current_seal, chained_seal = get_chained_seal(sealed_doc)

		frappe.db.set_value(self.reference_doctype, self.reference_docname, "_seal", current_seal, update_modified=False)

		self.hash = chained_seal
		self.data = frappe.as_json(sealed_doc, indent=4)

	def on_trash(self):
		raise frappe.PermissionError

	def on_cancel(self):
		raise frappe.PermissionError

def create_archive(doc):
	sealed_doc = get_sealed_doc(doc)
	if sealed_doc:
		try:
			archive = frappe.get_doc({
				"doctype": "Archived Document",
				"reference_doctype": doc.doctype,
				"reference_docname": doc.name,
				"timestamp": now_datetime(),
				"user": frappe.session.user,
				"data": sealed_doc
			})
			archive.flags.ignore_permissions = True
			archive.insert()
			archive.submit()
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Document archiving error")