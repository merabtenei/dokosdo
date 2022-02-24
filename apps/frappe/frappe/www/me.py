# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import frappe.www.list

no_cache = 1

def get_context(context):
	if frappe.session.user=='Guest':
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

	context.show_sidebar=True

	active_tokens = frappe.get_all("OAuth Bearer Token",\
		filters=[["user", "=", frappe.session.user]],\
		fields=["client"], distinct=True, order_by="creation")
	context.third_party_apps = True if active_tokens else False