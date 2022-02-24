// Copyright (c) 2020, Dokos SAS and Contributors
// See license.txt

import { Calendar } from '@fullcalendar/core';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import listPlugin from '@fullcalendar/list';
import interactionPlugin from '@fullcalendar/interaction';

frappe.ready(function() {
	frappe.provide("frappe.events");
	frappe.events.EventsPortalView = new EventsPortalView({
		parent: document.getElementById("events-calendar")
	});

});

class EventsPortalView {
	constructor(options) {
		Object.assign(this, options);
		this.show()
	}

	show() {
		frappe.require([
			'/assets/js/moment-bundle.min.js',
			'/assets/js/control.min.js'
		], () => {
			this.build_calendar()
		});
	}

	build_calendar() {
		this.calendarEl = $('<div id="calendar">').appendTo(this.parent);
		this.eventEl = $('<div id="event">').appendTo(this.parent);
		this.fullcalendar = new Calendar(
			this.calendarEl[0],
			this.calendar_options()
		)
		this.fullcalendar.render();
	}

	calendar_options() {
		return {
			eventClassNames: "events-calendar",
			initialView: frappe.is_mobile() ? "listDay" : "dayGridMonth",
			headerToolbar: {
				left: frappe.is_mobile() ? 'today' : 'dayGridMonth,timeGridWeek',
				center: "prev,title,next",
				right: frappe.is_mobile() ? "" : "prev,next today",
			},
			weekends: true,
			buttonText: {
				today: __("Today"),
				dayGridMonth: __("Month"),
				timeGridWeek: __("Week")

			},
			plugins: [
				dayGridPlugin,
				timeGridPlugin,
				interactionPlugin,
				listPlugin
			],
			locale: frappe.boot.lang || 'en',
			timeZone: frappe.boot.timeZone || 'UTC',
			events: this.getEvents,
			eventClick: this.eventClick,
			selectable: true,
			allDayContent: function() {
				return __("All Day");
			},
			height: "auto"
		}
	}

	getEvents(parameters, callback) {
		frappe.call({
			method: "frappe.desk.doctype.event.event.get_prepared_events",
			args: {
				start: moment(parameters.start).format("YYYY-MM-DD"),
				end: moment(parameters.end).format("YYYY-MM-DD"),
			}
		}).then(result => {
			callback(result.message)
		})
	}

	eventClick(event) {
		const dialog = new frappe.ui.Dialog ({
			size: 'large',
			title: __(event.event.title),
			fields: [{
				"fieldtype": "HTML",
				"fieldname": "event_description"
			}]
		});

		event.event.extendedProps.route&&dialog.set_primary_action(__("See details"), () => {
			window.location.href = event.event.extendedProps.route;
		})

		dialog.fields_dict.event_description.$wrapper.html(event_details(event));
		dialog.show()
	}
}


const event_details = (event) => {
	const image = event.event.extendedProps.image ? `<img class="card-img-top" src="${event.event.extendedProps.image}" alt="${event.event.extendedProps.subject}">` : "";
	const description = event.event.extendedProps.description ? `<p class="card-text">${event.event.extendedProps.description}</p>` : `<div>${__("No description")}</div>`;
	return `
		<div class="calendar-event">
			${image}
			<div class="card-body">
				<h5 class="card-title">${event.event.extendedProps.subject}</h5>
				${description}
			</div>
		</div>
	`
}