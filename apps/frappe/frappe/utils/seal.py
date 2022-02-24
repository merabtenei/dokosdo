# -*- coding: utf-8 -*-
# Copyright (c) 2021, Dokos and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime
from frappe.utils.data import DATETIME_FORMAT
import datetime
import hashlib

def get_sealed_doc(doc):
	timestamp = None
	if isinstance(doc._submitted, datetime.date):
		timestamp = datetime.datetime.strftime(doc._submitted, DATETIME_FORMAT)
	elif doc._submitted:
		timestamp = datetime.datetime.strftime(get_datetime(doc._submitted), DATETIME_FORMAT)

	sealed_doc = doc.as_dict().update({
		"doctype": doc.doctype,
		"docname": doc.name,
		"timestamp": timestamp
	})

	return sealed_doc

def get_chained_seal(doc):
	import uuid

	if not isinstance(doc, dict):
		doc = doc.as_dict()

	previous_seal = dict()

	if doc.get("timestamp"):
		previous_entry = frappe.db.sql("""
			SELECT name, _seal, _submitted
			FROM `tab%s`
			WHERE _submitted < '%s' AND _seal IS NOT NULL
			ORDER BY _submitted DESC LIMIT 1""" % (doc["doctype"],\
			doc.get("timestamp")), as_dict=True)

		if previous_entry:
			previous_seal = previous_entry[0]

	if not previous_seal:
		if frappe.db.get_global("initial_hash"):
			previous_seal['_seal'] = frappe.db.get_global("initial_hash")
		else:
			previous_seal['_seal'] = hash_line(uuid.uuid4().hex)
			frappe.db.set_global("initial_hash", previous_seal['_seal'])
			frappe.db.commit()

	current_seal = hash_line(doc)

	return current_seal, hash_chain(previous_seal['_seal'], current_seal)

def hash_line(data):
	sha = hashlib.sha256()
	sha.update(
		frappe.safe_encode(str(data))
	)
	return sha.hexdigest()

def hash_chain(prev, current):
	sha = hashlib.sha256()
	sha.update(
		frappe.safe_encode(str(prev)) + \
		frappe.safe_encode(str(current))
	)
	return sha.hexdigest()
