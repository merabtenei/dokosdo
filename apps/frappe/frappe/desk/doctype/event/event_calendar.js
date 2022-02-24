frappe.views.calendar["Event"] = {
	field_map: {
		"start": "starts_on",
		"end": "ends_on",
		"id": "name",
		"allDay": "all_day",
		"title": "subject",
		"status": "event_type",
		"color": "color",
		"rrule": "rrule",
		"secondary_status": "status"
	},
	secondary_status_color: {
		"Public": "green",
		"Private": "darkgray"
	},
	get_events_method: "frappe.desk.doctype.event.event.get_events"
}