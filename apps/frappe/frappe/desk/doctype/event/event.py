# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
from six.moves import range
from six import string_types
import frappe
import json

from frappe.utils import (getdate, cint, add_months, date_diff, add_days,
	nowdate, get_datetime_str, cstr, get_datetime, now_datetime, format_datetime)
from frappe import _
from frappe.website.website_generator import WebsiteGenerator
from frappe.utils.user import get_enabled_system_users
from frappe.desk.reportview import get_filters_cond
from frappe.desk.calendar import process_recurring_events
from frappe.integrations.doctype.google_calendar.google_calendar import get_google_calendar_object, \
	format_date_according_to_google_calendar, get_timezone_naive_datetime
from frappe.www.printview import get_html_and_style

weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
communication_mapping = {"": "Event", "Event": "Event", "Meeting": "Meeting", "Call": "Phone", "Sent/Received Email": "Email", "Other": "Other"}

FIELD_MAP = {
	"id": "name",
	"start": "starts_on",
	"end": "ends_on",
	"allDay": "all_day",
	"title": "subject",
	"description": "description",
	"route": "route",
	"published": "published"
}

class Event(WebsiteGenerator):
	def validate(self):
		if not self.starts_on:
			self.starts_on = now_datetime()

		# if start == end this scenario doesn't make sense i.e. it starts and ends at the same second!
		self.ends_on = None if self.starts_on == self.ends_on else self.ends_on

		if self.starts_on and self.ends_on:
			self.validate_from_to_dates("starts_on", "ends_on")

		if self.rrule and "DAILY" in self.rrule and self.ends_on and getdate(self.starts_on) != getdate(self.ends_on):
			frappe.throw(_("Daily Events should finish on the Same Day."))

		if self.sync_with_google_calendar and not self.google_calendar:
			frappe.throw(_("Select Google Calendar to which event should be synced."))

		self.set_route()

	def autoname(self):
		return

	def get_feed(self):
		return self.subject

	def set_route(self):
		if not self.route:
			self.route = f"events/{self.name}-{frappe.scrub(self.subject[:30])}"

	def before_save(self):
		if self.google_calendar and not self.google_calendar_id:
			self.google_calendar_id = frappe.db.get_value("Google Calendar", self.google_calendar, "google_calendar_id")

		if isinstance(self.rrule, list) and self.rrule > 1:
			self.rrule = self.rrule[0]


	def on_update(self):
		self.sync_communication()

	def on_trash(self):
		communications = frappe.get_all("Communication", dict(reference_doctype=self.doctype, reference_name=self.name))
		if communications:
			for communication in communications:
				frappe.delete_doc_if_exists("Communication", communication.name)

	def sync_communication(self):
		if self.event_participants:
			comms = []
			for participant in self.event_participants:
				filters = [
					["Communication", "reference_doctype", "=", self.doctype],
					["Communication", "reference_name", "=", self.name],
					["Communication Link", "link_doctype", "=", "Contact"],
					["Communication Link", "link_name", "=", participant.contact]
				]
				comms.extend(frappe.get_all("Communication", filters=filters, fields=["name"]))

			if comms:
				for comm in comms:
					communication = frappe.get_doc("Communication", comm.name)
					self.update_communication(self.event_participants, communication)
			else:
				self.create_communication(self.event_participants)

	def create_communication(self, participants):
		communication = frappe.new_doc("Communication")
		self.update_communication(participants, communication)
		self.communication = communication.name

	def update_communication(self, participants, communication):
		communication.communication_medium = "Event"
		communication.subject = self.subject
		communication.content = self.description if self.description else self.subject
		communication.communication_date = self.starts_on
		communication.sender = self.owner
		communication.sender_full_name = frappe.utils.get_fullname(self.owner)
		communication.reference_doctype = self.doctype
		communication.reference_name = self.name
		communication.communication_medium = communication_mapping.get(self.event_category) if self.event_category else ""
		communication.not_added_to_reference_timeline = 1
		communication.status = "Linked"
		communication.timeline_links = []
		for participant in participants:
			communication.add_link("Contact", participant.contact)
			contact = frappe.get_doc("Contact", participant.contact)
			if contact.links:
				for link in contact.links:
					if link.link_doctype and link.link_name:
						meta = frappe.get_meta(link.link_doctype)
						if hasattr(meta, "allow_events_in_timeline") and meta.allow_events_in_timeline == 1:
							communication.add_link(link.link_doctype, link.link_name)

		communication.save(ignore_permissions=True)

	def add_participant(self, contact):
		"""Add a single participant to event participants
		Args:
			contact (string): Contact name
		"""
		self.append("event_participants", {
			"contact": contact,
		})

	def add_participants(self, participants):
		"""Add participant entry
		Args:
			participants ([Array]): Array of contact names
		"""
		for participant in participants:
			self.add_participant(participant)

	def remove_participant(self, participant):
		participant_list = []
		for event_participant in self.event_participants:
			if event_participant != participant:
				participant_list.append(event_participant)

		self.event_participants = participant_list

	def get_context(self, context):
		if not cint(self.published):
			self.show_permission_error()

		if self.visible_for != "All":
			if frappe.session.user =="Guest":
				self.show_permission_error()
			elif self.visible_for == "Role" and self.role not in frappe.get_roles(frappe.session.user):
				self.show_permission_error()

		is_guest = frappe.session.user == "Guest"

		context.no_cache = 0
		context.show_sidebar = not is_guest
		context.show_close_button = not is_guest

		content = f'<p class="card-text">{self.description or ""}</p>'
		event_style = ""
		if self.portal_print_format:
			print_format_content = self.print_format_content()
			content = print_format_content.get("html")
			event_style = print_format_content.get("style")

		context.content = content
		context.event_style = event_style

		fields = []
		for field in frappe.get_meta("Event Registration").fields:
			if not (field.fieldname == "amended_from" or field.permlevel > 0):
				field.label = _(field.label)
				fields.append(field)

		context.registration_form = frappe.as_json(fields)
		context.is_registered = frappe.db.exists("Event Registration", dict(user=frappe.session.user, event=self.name, docstatus=1))

		context.attachments = frappe.get_all("File", fields=["name", "file_name", "file_url"],
			filters = {"attached_to_name": self.name, "attached_to_doctype": "Event", "is_private": 0}) if self.display_public_files else []

	def print_format_content(self):
		frappe.flags.ignore_print_permissions = True
		return get_html_and_style(self, print_format=self.portal_print_format)

	def show_permission_error(self):
		frappe.throw(_("This event is not publicly available"), frappe.PermissionError)

@frappe.whitelist()
def delete_communication(event, reference_doctype, reference_docname):
	deleted_participant = frappe.get_doc(reference_doctype, reference_docname)
	if isinstance(event, string_types):
		event = json.loads(event)

	filters = [
		["Communication", "reference_doctype", "=", event.get("doctype")],
		["Communication", "reference_name", "=", event.get("name")],
		["Communication Link", "link_doctype", "=", deleted_participant.reference_doctype],
		["Communication Link", "link_name", "=", deleted_participant.reference_docname]
	]

	comms = frappe.get_list("Communication", filters=filters, fields=["name"])

	if comms:
		deletion = []
		for comm in comms:
			delete = frappe.get_doc("Communication", comm.name).delete()
			deletion.append(delete)

		return deletion

	return {}


def get_permission_query_conditions(user):
	if not user: user = frappe.session.user
	return """(`tabEvent`.`event_type`='Public' or `tabEvent`.`owner`=%(user)s)""" % {
			"user": frappe.db.escape(user),
		}

def has_permission(doc, user):
	if doc.event_type == "Public" or doc.owner == user:
		return True

	return False

def send_event_digest():
	today = nowdate()
	for user in get_enabled_system_users():
		events = get_events(today, today, user.name, for_reminder=True)
		if events:
			frappe.set_user_lang(user.name, user.language)

			for e in events:
				e.starts_on = format_datetime(e.starts_on, 'hh:mm a')
				if e.all_day:
					e.starts_on = "All Day"

			frappe.sendmail(
				recipients=user.email,
				subject=frappe._("Upcoming Events for Today"),
				template="upcoming_events",
				args={
					'events': events,
				},
				header=[frappe._("Events in Today's Calendar"), 'blue']
			)

@frappe.whitelist()
def get_events(start, end, user=None, for_reminder=False, filters=None, field_map=None):
	if not user:
		user = frappe.session.user

	if isinstance(filters, string_types):
		filters = json.loads(filters)

	additional_fields = ""
	if field_map:
		additional_fields = ", " + ", ".join([f"`tabEvent`.{f}" for f in frappe.parse_json(field_map).values()])

	filter_condition = get_filters_cond('Event', filters, [])

	tables = ["`tabEvent`"]
	if "`tabEvent Participants`" in filter_condition:
		tables.append("`tabEvent Participants`")

	events = frappe.db.sql("""
		SELECT `tabEvent`.name,
				`tabEvent`.subject,
				`tabEvent`.description,
				`tabEvent`.color,
				`tabEvent`.starts_on,
				`tabEvent`.ends_on,
				`tabEvent`.owner,
				`tabEvent`.all_day,
				`tabEvent`.event_type,
				`tabEvent`.repeat_this_event,
				`tabEvent`.rrule,
				`tabEvent`.repeat_till
				{additional_fields}
		FROM {tables}
		WHERE (
				(
					(date(`tabEvent`.starts_on) BETWEEN date(%(start)s) AND date(%(end)s))
					OR (date(`tabEvent`.ends_on) BETWEEN date(%(start)s) AND date(%(end)s))
					OR (
						date(`tabEvent`.starts_on) <= date(%(start)s)
						AND date(`tabEvent`.ends_on) >= date(%(end)s)
					)
				)
				OR (
					date(`tabEvent`.starts_on) <= date(%(start)s)
					AND `tabEvent`.repeat_this_event=1
					AND coalesce(`tabEvent`.repeat_till, '3000-01-01') > date(%(start)s)
				)
			)
		{reminder_condition}
		{filter_condition}
		AND (
				`tabEvent`.event_type='Public'
				OR `tabEvent`.owner=%(user)s
				OR EXISTS(
					SELECT `tabDocShare`.name
					FROM `tabDocShare`
					WHERE `tabDocShare`.share_doctype='Event'
						AND `tabDocShare`.share_name=`tabEvent`.name
						AND `tabDocShare`.user=%(user)s
				)
			)
		ORDER BY `tabEvent`.starts_on""".format(
			additional_fields=additional_fields,
			tables=", ".join(tables),
			filter_condition=filter_condition,
			reminder_condition="AND coalesce(`tabEvent`.send_reminder, 0)=1" if for_reminder else ""
		), {
			"start": start,
			"end": end,
			"user": user,
		}, as_dict=1)

	# process recurring events
	result = []
	for event in events:
		result.append(event)
		if event.get("repeat_this_event"):
			result = [x for x in result if x.get("name") != event.get("name")]
			start = get_datetime(start).replace(hour=0, minute=0, second=0) if event.get("all_day") else start
			end = get_datetime(end).replace(hour=23, minute=59, second=0) if event.get("all_day") else end
			result.extend(process_recurring_events(event, start, end, "starts_on", "ends_on", "rrule"))

	return result

# Close events if ends_on or repeat_till is less than now_datetime
def set_status_of_events():
	events = frappe.get_list("Event", filters={"status": "Open"}, \
		fields=["name", "ends_on", "repeat_till"])
	for event in events:
		if (event.ends_on and getdate(event.ends_on) < getdate(nowdate())) \
			or (event.repeat_till and getdate(event.repeat_till) < getdate(nowdate())):

			frappe.db.set_value("Event", event.name, "status", "Closed")

def insert_event_to_calendar(account, event, recurrence=None):
	"""
		Inserts event in Frappe Calendar during Sync
	"""
	calendar_event = {
		"doctype": "Event",
		"subject": event.get("summary"),
		"description": event.get("description"),
		"sync_with_google_calendar": 1,
		"google_calendar": account.name,
		"google_calendar_id": account.google_calendar_id,
		"google_calendar_event_id": event.get("id"),
		"rrule": recurrence,
		"starts_on": get_datetime(start.get("date")) if start.get("date") \
			else get_timezone_naive_datetime(start),
		"ends_on": get_datetime(end.get("date")) if end.get("date") else get_timezone_naive_datetime(end),
		"all_day": 1 if start.get("date") else 0,
		"repeat_this_event": 1 if recurrence else 0
	}
	doc = frappe.get_doc(calendar_event)
	doc.flags.pulled_from_google_calendar = True
	doc.insert(ignore_permissions=True)

def update_event_in_calendar(account, event, recurrence=None):
	"""
		Updates Event in Frappe Calendar if any existing Google Calendar Event is updated
	"""
	calendar_event = frappe.get_doc("Event", {"google_calendar_event_id": event.get("id")})
	calendar_event.subject = event.get("summary")
	calendar_event.description = event.get("description")
	calendar_event.rrule = recurrence
	calendar_event.starts_on = get_datetime(start.get("date")) if start.get("date") \
		else get_timezone_naive_datetime(start)
	calendar_event.ends_on = get_datetime(end.get("date")) if end.get("date") \
		else get_timezone_naive_datetime(end)
	calendar_event.all_day = 1 if start.get("date") else 0
	calendar_event.repeat_this_event = 1 if recurrence else 0
	calendar_event.flags.pulled_from_google_calendar = True
	calendar_event.save(ignore_permissions=True)

def close_event_in_calendar(account, event):
	# If any synced Google Calendar Event is cancelled, then close the Event
	frappe.db.set_value("Event", {"google_calendar_id": account.google_calendar_id, \
		"google_calendar_event_id": event.get("id")}, "status", "Closed")
	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "Event",
		"reference_name": frappe.db.get_value("Event", {"google_calendar_id": account.google_calendar_id, \
			"google_calendar_event_id": event.get("id")}, "name"),
		"content": " - Event deleted from Google Calendar.",
	}).insert(ignore_permissions=True)

def insert_event_in_google_calendar(doc, method=None):
	"""
		Insert Events in Google Calendar if sync_with_google_calendar is checked.
	"""
	if not frappe.db.exists("Google Calendar", {"name": doc.google_calendar}) \
		or doc.flags.pulled_from_google_calendar or not doc.sync_with_google_calendar:
		return

	google_calendar, account = get_google_calendar_object(doc.google_calendar)

	if not account.push_to_google_calendar:
		return

	event = {
		"summary": doc.subject,
		"description": doc.description,
		"sync_with_google_calendar": 1,
		"recurrence": [doc.rrule] if doc.rrule else None
	}
	event.update(format_date_according_to_google_calendar(doc.all_day, get_datetime(doc.starts_on), \
		get_datetime(doc.ends_on)))

	try:
		event = google_calendar.events().insert(calendarId=doc.google_calendar_id, body=event).execute()
		doc.db_set("google_calendar_event_id", event.get("id"), update_modified=False)
		frappe.publish_realtime('event_synced', {"message": _("Event Synced with Google Calendar.")}, \
			user=frappe.session.user)
	except HttpError as err:
		frappe.msgprint(f'{_("Google Error")}: {json.loads(err.content)["error"]["message"]}')
		frappe.throw(_("Google Calendar - Could not insert event in Google Calendar {0}, error code {1}."\
			).format(account.name, err.resp.status))

def update_event_in_google_calendar(doc, method=None):
	"""
		Updates Events in Google Calendar if any existing event is modified in Frappe Calendar
	"""
	# Workaround to avoid triggering updation when Event is being inserted since
	# creation and modified are same when inserting doc
	if not frappe.db.exists("Google Calendar", {"name": doc.google_calendar}) \
		or doc.modified == doc.creation or not doc.sync_with_google_calendar \
		or doc.flags.pulled_from_google_calendar:
		return

	if doc.sync_with_google_calendar and not doc.google_calendar_event_id:
		# If sync_with_google_calendar is checked later, then insert the event rather than updating it.
		insert_event_in_google_calendar(doc)
		return

	google_calendar, account = get_google_calendar_object(doc.google_calendar)

	if not account.push_to_google_calendar:
		return

	try:
		event = google_calendar.events().get(calendarId=doc.google_calendar_id, \
			eventId=doc.google_calendar_event_id).execute()
		event["summary"] = doc.subject
		event["description"] = doc.description
		event["recurrence"] = [doc.rrule] if doc.rrule else None
		event["status"] = "cancelled" if doc.event_type == "Cancelled" \
			or doc.status == "Closed" else event.get("status")
		event.update(format_date_according_to_google_calendar(doc.all_day, get_datetime(doc.starts_on), \
			get_datetime(doc.ends_on)))

		google_calendar.events().update(calendarId=doc.google_calendar_id, \
			eventId=doc.google_calendar_event_id, body=event).execute()
		frappe.publish_realtime('event_synced', {"message": _("Event Synced with Google Calendar.")}, \
			user=frappe.session.user)
	except HttpError as err:
		frappe.msgprint(f'{_("Google Error")}: {json.loads(err.content)["error"]["message"]}')
		frappe.throw(_("Google Calendar - Could not update Event {0} in Google Calendar, error code {1}."\
			).format(doc.name, err.resp.status))

def delete_event_in_google_calendar(doc, method=None):
	"""
		Delete Events from Google Calendar if Frappe Event is deleted.
	"""

	if not frappe.db.exists("Google Calendar", {"name": doc.google_calendar}) \
		or doc.flags.pulled_from_google_calendar:
		return

	google_calendar, account = get_google_calendar_object(doc.google_calendar)

	if not account.push_to_google_calendar:
		return

	try:
		event = google_calendar.events().get(calendarId=doc.google_calendar_id, \
			eventId=doc.google_calendar_event_id).execute()
		event["recurrence"] = None
		event["status"] = "cancelled"

		google_calendar.events().update(calendarId=doc.google_calendar_id, \
			eventId=doc.google_calendar_event_id, body=event).execute()
	except HttpError as err:
		frappe.msgprint(f'{_("Google Error")}: {json.loads(err.content)["error"]["message"]}')
		frappe.msgprint(_("Google Calendar - Could not delete Event {0} from Google Calendar, error code {1}."\
			).format(doc.name, err.resp.status))

@frappe.whitelist(allow_guest=True)
def get_prepared_events(start, end):
	events = get_events(start, end, field_map={"route": "route", "published": "published", "image": "image", "visible_for": "visible_for", "role": "role"})
	roles = frappe.get_roles(frappe.session.user)

	for event in events:
		if event.get("published") and (event.get("visible_for") == "All" or (event.get("visible_for") == "Role" and event.get("role") in roles)):
			for field in FIELD_MAP:
				event.update({
					field: event.get(FIELD_MAP[field])
				})

	return events