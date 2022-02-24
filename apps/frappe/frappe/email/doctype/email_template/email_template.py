# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe.model.document import Document
from frappe.utils.jinja import validate_template
from six import string_types
from frappe import _

class EmailTemplate(Document):
	def validate(self):
		if self.use_html:
			validate_template(self.response_html)
		else:
			validate_template(self.response)

	def get_formatted_subject(self, doc):
		return frappe.render_template(self.subject, doc)

	def get_formatted_response(self, doc):
		if self.use_html:
			return frappe.render_template(self.response_html, doc)

		return frappe.render_template(self.response, doc)

	def get_formatted_email(self, doc):
		if isinstance(doc, string_types):
			doc = json.loads(doc)

		return {
			"subject" : self.get_formatted_subject(doc),
			"message" : self.get_formatted_response(doc)
		}

@frappe.whitelist()
def get_email_template(template_name, doc):
	'''Returns the processed HTML of a email template with the given doc'''
	if isinstance(doc, string_types):
		doc = json.loads(doc)

	email_template = frappe.get_doc("Email Template", template_name)
	return email_template.get_formatted_email(doc)

@frappe.whitelist()
def get_template_fields(reference):
	meta = frappe.get_meta(reference)

	result = {}
	links = []

	result["name"] = [{
		"fieldname": "name",
		"label": _("Name"),
		"fieldtype": "Data",
		"parent": meta.name,
		"reference": "name",
		"function": get_fieldtype_related_function("Data")
	}]
	for field in meta.fields:
		result = add_field_to_results(result, field, "name")

		if field.fieldtype == "Link":
			links.append({
				"doctype": field.options,
				"reference_label": field.label,
				"reference_name": field.fieldname
			})

	result["Custom Functions"] = add_custom_functions()

	for link in links:
		link_meta = frappe.get_meta(link["doctype"])
		result[link["reference_name"]] = [{
			"fieldname": "name",
			"label": _("Name"),
			"fieldtype": "Data",
			"parent": link_meta.name,
			"reference": link["reference_name"],
			"function": get_fieldtype_related_function("Data"),
			"reference_label": link["reference_label"]
		}]
		for field in link_meta.fields:
			result = add_field_to_results(result, field, link["reference_name"])

	return result

def add_field_to_results(result, field, reference):
	if field.fieldtype not in ["Column Break", "Section Break", "Button"] and field.print_hide != 1 and field.label:
		result[reference].append({
			"fieldname": field.fieldname,
			"label": _(field.label),
			"fieldtype": field.fieldtype,
			"parent": field.parent,
			"reference": reference,
			"function": get_fieldtype_related_function(field.fieldtype)
		})

	return result

def add_custom_functions():
	functions = []

	# Current date
	functions.append({
		"fieldname": None,
		"label": _("Current Date"),
		"fieldtype": None,
		"parent": "Custom Functions",
		"reference": None,
		"function": "frappe.format_date(frappe.utils.getdate(frappe.utils.nowdate()))"
	})

	for method in frappe.get_hooks('jinja_template_functions'):
		functions = frappe.get_attr(method)(functions)

	return functions

def get_fieldtype_related_function(fieldtype):
	if fieldtype in ["Date", "Datetime"]:
		return "frappe.format_date"

	else:
		return None