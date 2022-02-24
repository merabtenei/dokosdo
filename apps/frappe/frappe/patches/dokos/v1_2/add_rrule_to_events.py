import frappe
from frappe.desk.calendar import get_rrule

def execute():

	frappe.reload_doc('desk', 'doctype', 'event')

	events = frappe.get_all("Event", filters={"repeat_this_event": 1})

	for event in events:
		rrule = get_rrule(event)
		if rrule:
			frappe.db.set_value("Event", event.name, "rrule", rrule)
