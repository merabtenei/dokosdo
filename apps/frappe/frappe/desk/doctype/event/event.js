// Copyright (c) 2019, Dokos SAS and Contributors
// MIT License. See license.txt
frappe.provide("frappe.desk");

frappe.ui.form.on("Event", {
	setup() {
		frappe.realtime.on('event_synced', (data) => {
			frappe.show_alert({message: data.message, indicator: 'green'});
		})
	},
	onload: function(frm) {
		frm.set_query('google_calendar', function() {
			return {
				filters: {
					"user": ['in', [frappe.session.user, null]],
					"reference_document": frm.doctype
				}
			};
		});
	},
	refresh: function(frm) {
		frm.trigger('add_repeat_text')
	},
	repeat_this_event: function(frm) {
		if(frm.doc.repeat_this_event === 1) {
			new frappe.CalendarRecurrence({frm: frm, show: true});
		}
	},
	add_repeat_text(frm) {
		if (frm.doc.rrule) {
			new frappe.CalendarRecurrence({frm: frm, show: false});
		}
	},
	sync_with_google_calendar(frm) {
		frappe.db.get_value("Google Calendar", {user: frappe.session.user}, "name", r => {
			r&&r.name&&frm.set_value("google_calendar", r.name)
		})
	}
});
