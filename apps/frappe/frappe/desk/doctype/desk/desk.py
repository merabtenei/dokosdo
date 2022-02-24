# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from frappe import _

WIDTH_MAP = {
	"Third": 33,
	"Half": 50,
	"Full": 100
}

class Desk(Document):
	pass

def has_permission(doc, ptype, user):
	if "System Manager" in frappe.get_roles(user):
		return True
	else:
		return doc.owner == user

@frappe.whitelist()
def get_desk(user):
	desk_data = frappe.db.sql("""
		SELECT
			di.name, di.widget_height, di.widget_width, di.widget_type,
			dca.source_document, dca.user,
			dch.chart_name, dch.type, dch.source as chart_source, dch.chart_type, dch.width, 
			dch.timeseries, dch.time_interval, dch.timespan as chart_timespan, dch.unit,
			dch.color as chart_color, dch.filters_json, dch.last_synced_on as chart_last_synced,
			dcc.card_name, dcc.source as card_source, dcc.timespan as card_timespan, dcc.color as card_color,
			dcc.icon, dcc.last_synced_on as card_last_synced, dcc.card_type
		FROM
			`tabDesk Items` di
		LEFT JOIN
			`tabDashboard Calendar` dca
		ON
			di.widget_type='Dashboard Calendar' AND di.widget_name=dca.name
		LEFT JOIN
			`tabDashboard Chart` dch
		ON
			di.widget_type='Dashboard Chart' AND di.widget_name=dch.name
		LEFT JOIN
			`tabDashboard Card` dcc
		ON
			di.widget_type='Dashboard Card' AND di.widget_name=dcc.name
		WHERE
			di.parent = %s
		ORDER BY
			di.idx ASC
	""", (user), as_dict=True)

	for data in desk_data:
		for item in ["chart_timespan", "card_timespan"]:
			data[item] = _(data[item])

	return desk_data

@frappe.whitelist()
def get_module_dashboard(user, module):
	parent = frappe.db.get_value("Module Dashboard", dict(user=frappe.session.user, module=module), "name")

	return frappe.db.sql("""
		SELECT
			mdi.name, mdi.widget_width, mdi.widget_type,
			dch.chart_name, dch.type, dch.source as chart_source, dch.chart_type, 
			dch.width, dch.timeseries, dch.time_interval, dch.unit, dch.last_synced_on as chart_last_synced,
			dch.timespan as chart_timespan, dch.color as chart_color, dch.filters_json,
			dcc.card_name, dcc.source as card_source, dcc.timespan as card_timespan,
			dcc.color as card_color, dcc.icon, dcc.last_synced_on as card_last_synced, dcc.card_type
		FROM
			`tabModule Dashboard Items` mdi
		LEFT JOIN
			`tabDashboard Chart` dch
		ON
			mdi.widget_type='Dashboard Chart' AND mdi.widget_name=dch.name
		LEFT JOIN
			`tabDashboard Card` dcc
		ON
			mdi.widget_type='Dashboard Card' AND mdi.widget_name=dcc.name
		WHERE
			mdi.parent = %s
		ORDER BY
			mdi.idx ASC
	""", (parent), as_dict=True)

@frappe.whitelist()
def create_user_desk(user):
	desk = frappe.new_doc("Desk")
	desk.user = user
	desk.insert(ignore_permissions=True)

	return desk

@frappe.whitelist()
def add_widget(origin, widget_type, **kwargs):
	widget_type = json.loads(widget_type)[0]
	options = json.loads(kwargs['args'])

	widget_creator = WidgetCreator(origin)
	widget_creator.add_widget(widget_type, **options)

@frappe.whitelist()
def remove_widget(origin, widget):
	if not isinstance(widget, list):
		widget = json.loads(widget)

	if origin == "Desk":
		desk = frappe.get_doc("Desk", frappe.session.user)
		desk.desk_items = [x for x in desk.desk_items if x.name !=widget[0]["name"]]
		desk.save()
	else:
		dash = frappe.get_doc("Module Dashboard", dict(user=frappe.session.user, module=origin))
		dash.module_dashboard_items = [x for x in dash.module_dashboard_items if x.name !=widget[0]["name"]]
		dash.save()

@frappe.whitelist()
def register_positions(items):
	if not isinstance(items, list):
		items = json.loads(items)

	i = 1
	for item in items:
		frappe.db.set_value("Desk Items", item, "idx", i, update_modified=False)
		i += 1

	return "done"

@frappe.whitelist()
def check_widget_width(module, widget_type, value):
	value_width = float(WIDTH_MAP[frappe.db.get_value(widget_type, value, "width")]) if widget_type == "Dashboard Chart" else 20
	module_dashboard = get_module_dashboard_doc(frappe.session.user, module)

	current_width = 0
	for item in module_dashboard.module_dashboard_items:
		current_width += float(item.widget_width)

	return False if current_width + value_width > 100 else True

def get_module_dashboard_doc(user, module):
	if frappe.db.exists("Module Dashboard", dict(user=user, module=module)):
		return frappe.get_doc("Module Dashboard", dict(user=user, module=module))

	else:
		new_dashboard = frappe.new_doc("Module Dashboard")
		new_dashboard.user = user
		new_dashboard.module = module
		new_dashboard.insert(ignore_permissions=True)

		return new_dashboard

class WidgetCreator:
	def __init__(self, origin, user=None):
		self.origin = origin
		self.target = origin if origin == "Desk" else "Module"
		self.user = user if user else frappe.session.user
		self.doc = frappe.get_doc("Desk", self.user) if self.origin == "Desk" \
			else get_module_dashboard_doc(self.user, self.origin)

		self.widgets_map = {
			'Dashboard Calendar': {
				"Desk": self._add_calendar
			},
			'Dashboard Chart': {
				"Desk": self._add_chart,
				"Module": self._add_module_chart,
			},
			'Dashboard Card': {
				"Desk": self._add_stats,
				"Module": self._add_module_stats,
			}
		}

	def add_widget(self, widget_type, **kwargs):
		creator = self._get_creator(widget_type)
		if not creator:
			raise ValueError(widget_type)
		return creator(**kwargs)

	def _get_creator(self, widget_type):
		return self.widgets_map[widget_type][self.target]

	def _add_calendar(self, **kwargs):
		if frappe.db.exists("Dashboard Calendar", {"source_document": kwargs["reference"], "user": kwargs["user"]}):
			widget_name = frappe.db.get_value("Dashboard Calendar", \
				{"source_document": kwargs["reference"], "user": kwargs["user"]}, "name")

		else:
			new_desk_calendar = frappe.get_doc({
				"doctype": "Dashboard Calendar",
				"source_document": kwargs["reference"],
				"user": kwargs["user"]
			}).insert()
			widget_name = new_desk_calendar.name
		
		self.__add_to_desk("Dashboard Calendar", widget_name, 33, 400)

	def _add_chart(self, **kwargs):
		chart_width = get_chart_width(kwargs["chart"])
		self.__add_to_desk("Dashboard Chart", kwargs["chart"], chart_width, 340)

	def _add_stats(self, **kwargs):
		self.__add_to_desk("Dashboard Card", kwargs["card"], 25, 175)

	def _add_module_chart(self, **kwargs):
		chart_width = get_chart_width(kwargs["chart"])
		self.__add_to_module_dashboard("Dashboard Chart", kwargs["chart"], chart_width)

	def _add_module_stats(self, **kwargs):
		self.__add_to_module_dashboard("Dashboard Card", kwargs["card"], 20)

	def __add_to_desk(self, widget_type, widget_name, width=50, height=400):
		self.doc.append("desk_items", {
			"widget_type": widget_type,
			"widget_name": widget_name,
			"widget_width": width,
			"widget_height": height
		})
		self.doc.save()

	def __add_to_module_dashboard(self, widget_type, widget_name, width=50):
		self.doc.append("module_dashboard_items", {
			"widget_type": widget_type,
			"widget_name": widget_name,
			"widget_width": width
		})
		self.doc.save()

def get_chart_width(chart):
	set_width = frappe.db.get_value("Dashboard Chart", chart, "width")

	return WIDTH_MAP[set_width]