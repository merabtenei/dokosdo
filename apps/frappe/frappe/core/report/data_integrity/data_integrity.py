# Copyright (c) 2021, Dokos SAS and contributors
# For license information, please see license.txt

import frappe
from collections import defaultdict
from frappe import _
from frappe.utils import get_datetime
from frappe.utils.seal import hash_chain

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_data(filters=None):
	if filters is None:
		return []

	archives_list = get_archives(filters)
	archives = get_archives_dict(archives_list)
	documents = get_documents(filters)

	doc_dict = defaultdict(dict)
	for document in documents:
		doc_dict[document.name] = {
			"seal": document._seal or "",
			"submission_date": document._submitted or "",
			"submitted_by": document._submitted_by or "",
			"archive": archives.get(document.name, {})
		}

	missing_keys = []
	for key in archives.keys():
		if key not in doc_dict.keys():
			missing_keys.append(key)

	for missing_key in missing_keys:
		doc_dict[missing_key] = {
			"seal": "",
			"submission_date": "",
			"submitted_by": "",
			"archive": archives.get(missing_key, {})
		}

	data = []
	documents_list = [x.name for x in sorted(documents, key=lambda i: get_datetime(i["_submitted"]))]
	documents_dict = get_documents_dict(documents)

	for doc in doc_dict:
		archive = doc_dict[doc].get("archive", {})
		icon, comments = check_integrity(doc, doc_dict[doc], documents_list, documents_dict, archives)
		row = {
			"document_name": doc,
			"submission_date": doc_dict[doc].get("submission_date"),
			"submitted_by": doc_dict[doc].get("submitted_by"),
			"archive": archive.get("name", ""),
			"comments": comments,
			"icon": icon
		}

		data.append(row)

	return data

def get_documents(filters):
	return frappe.get_all(
		filters.get("doctype"),
		filters={"docstatus": [">", 0]},
		fields=["name", "_seal", "_submitted", "_submitted_by"],
		order_by="name desc"
	)

def get_documents_dict(documents):
	return {x.name: x._seal for x in documents}

def get_archives(filters):
	return frappe.get_all(
		"Archived Document",
		filters={"reference_doctype": filters.get("doctype")},
		fields=["name", "timestamp", "hash", "reference_docname", "data", "creation"],
		order_by="creation"
	)

def get_archives_dict(archives):
	return {x.reference_docname: x for x in archives}

def check_integrity(name, doc, documents_list, documents_dict, archives):
	if not doc.get("seal"):
		return "error", _("This document is not sealed")

	archive = doc.get("archive", {})
	if not archive.get("name"):
		return "warning", _("This document is not archived")
	else:
		seal = doc.get("seal")
		initial_hash = frappe.db.get_global("initial_hash")
		previous_archive = documents_list.index(name)
		if previous_archive > 0:
			previous_doc = documents_list[previous_archive - 1]
			previous_chain = documents_dict.get(previous_doc)
		else:
			previous_chain = initial_hash

		msg = ""
		if hash_chain(previous_chain, seal) != archive.get("hash"):
			msg = "warning", _("The seal chain does not match")
		if hash_chain(initial_hash, seal) == archive.get("hash"):
			msg = "warning", _("The document exists but is not chained correctly")
		if msg:
			return msg

	return "success", _("This document exists and has been correctly archived")


def get_columns(filters=None):
	columns = [
		{
			"label": _("Document Name"),
			"fieldname": "document_name",
			"fieldtype": "Data",
			"width": 300
		},
		{
			"label": _("Submission Date"),
			"fieldname": "submission_date",
			"fieldtype": "Datetime",
			"width": 200
		},
		{
			"label": _("Submitted By"),
			"fieldname": "submitted_by",
			"fieldtype": "Link",
			"options": "User",
			"width": 200
		},
		{
			"label": _("Archive"),
			"fieldname": "archive",
			"fieldtype": "Link",
			"options": "Archived Document",
			"width": 300
		},
		{
			"label": _("Comments"),
			"fieldname": "comments",
			"fieldtype": "Data",
			"width": 300
		}
	]
	return columns

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def query_doctypes(doctype, txt, searchfield, start, page_len, filters):
	user = frappe.session.user
	user_perms = frappe.utils.user.UserPermissions(user)
	user_perms.build_permissions()
	can_read = user_perms.can_read

	sealed_doctypes = [d[0] for d in frappe.db.get_values("DocType", {"is_sealed": 1})]

	out = []
	for dt in can_read:
		if txt.lower().replace("%", "") in _(dt).lower() and dt in sealed_doctypes:
			out.append([dt])

	return out