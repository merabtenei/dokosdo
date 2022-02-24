# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from __future__ import unicode_literals

import frappe

def get_context(context):
	context.no_cache = 1
	if frappe.local.form_dict.get("token"):
		token = frappe.local.form_dict.token

	doc = None
	if frappe.local.form_dict.get("doctype") and frappe.local.form_dict.get("docname"):
		doc = frappe.get_doc(frappe.local.form_dict.doctype, frappe.local.form_dict.docname)

	context.payment_message = ''
	if doc and hasattr(doc, 'get_payment_success_message'):
		context.payment_message = doc.get_payment_success_message()

