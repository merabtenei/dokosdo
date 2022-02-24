// Copyright (c) 2019, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Notification Settings', {
	onload: (frm) => {
		frappe.breadcrumbs.add({
			label: __('Settings'),
			route: '/app/workspace/Settings',
			type: 'Custom'
		});

		frm.set_query('subscribed_documents', () => {
			return {
				filters: {
					istable: 0
				}
			};
		});
	},

	refresh: (frm) => {
		frm.trigger('setup_calendar_options')
		if (frappe.user.has_role('System Manager')) {
			frm.add_custom_button(__('Go to Notification Settings List'), () => {
				frappe.set_route('List', 'Notification Settings');
			});
		}
	},

	setup_calendar_options(frm) {
		frappe.xcall('frappe.desk.doctype.notification_settings.notification_settings.get_calendar_options')
		.then(r => {
			frm.fields_dict.default_calendar.df.options = r;
			frm.refresh_field('default_calendar');
		})
	}
});