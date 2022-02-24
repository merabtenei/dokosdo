# -*- coding: utf-8 -*-
# Copyright (c) 2019, Dokos and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import datetime
from frappe.model.document import Document
from frappe.utils.dashboard import cache_source
from frappe.utils.dateutils import get_from_date_from_timespan
from frappe.utils import nowdate, add_to_date, getdate, get_last_day
from frappe.desk.doctype.dashboard_chart.dashboard_chart import get_aggregate_function

@frappe.whitelist()
def get(card_name=None, card=None, no_cache=None, from_date=None, to_date=None, refresh=None):
	if card_name:
		card = frappe.get_doc('Dashboard Card', card_name)
	else:
		card = frappe._dict(frappe.parse_json(card))

	card = frappe.parse_json(card)
	timespan = card.timespan
	filters = frappe.parse_json(card.filters_json) or {}

	# don't include cancelled documents
	filters['docstatus'] = ('<', 2)

	if not from_date:
		from_date = get_from_date_from_timespan(to_date, timespan)
	if not to_date:
		to_date = datetime.datetime.now()

	# get conditions from filters
	conditions, values = frappe.db.build_conditions(filters)

	# query will return year, unit and aggregate value
	data = frappe.db.sql('''
		select
			{aggregate_function}({value_field})
		from `tab{doctype}`
		where
			{conditions}
			and {datefield} >= '{from_date}'
			and {datefield} <= '{to_date}'
	'''.format(
		datefield=card.based_on,
		aggregate_function=get_aggregate_function(card.card_type),
		value_field=card.value_based_on or '1',
		doctype=card.document_type,
		conditions=conditions,
		from_date=from_date.strftime('%Y-%m-%d'),
		to_date=to_date
	), values, as_list=True)

	if len(data) > 0:
		return data[0][0]
	else:
		return None

class DashboardCard(Document):
	def on_update(self):
		frappe.cache().delete_key('card-data:{}'.format(self.name))

	def validate(self):
		if self.card_type != 'Custom':
			self.check_required_field()
		self.check_document_type()

	def check_required_field(self):
		if not self.card_type=="Custom":
			if not self.based_on:
				frappe.throw(_("Time series based on is required to create a dashboard card"))
			if not self.document_type:
				frappe.throw(_("Document type is required to create a dashboard card"))

	def check_document_type(self):
		if frappe.get_meta(self.document_type).issingle:
			frappe.throw(_("You cannot create a dashboard chart from single DocTypes"))
