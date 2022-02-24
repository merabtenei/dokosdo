# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint
from frappe.model.document import Document

class ScheduledJobLog(Document):
	pass

def flush():
	if cint(frappe.get_system_settings("restricted_jobs_logs")):
		frappe.db.sql("""
			DELETE FROM `tabScheduled Job Log`
			WHERE datediff(curdate(), creation) > 30
		""")