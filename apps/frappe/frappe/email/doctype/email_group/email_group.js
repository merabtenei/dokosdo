// Copyright (c) 2016, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Email Group", "refresh", function(frm) {
	if(!frm.is_new()) {
		frm.add_custom_button(__("Import Subscribers"), function() {
			new SubscriberImportDialog({frm: frm})
		}, __("Action"));

		frm.add_custom_button(__("Add Subscribers"), function() {
			frappe.prompt({fieldtype:"Text",
				label:__("Email Addresses"), fieldname:"email_list", reqd:1},
				function(data) {
					frappe.call({
						method: "frappe.email.doctype.email_group.email_group.add_subscribers",
						args: {
							"name": frm.doc.name,
							"email_list": data.email_list
						},
						callback: function(r) {
							frm.set_value("total_subscribers", r.message);
						}
					})
				}, __("Add Subscribers"), __("Add"));
		}, __("Action"));

		frm.add_custom_button(__("New Newsletter"), function() {
			frappe.new_doc("Newsletter");
		}, __("Action"));

	}
});

class SubscriberImportDialog {
	constructor(opts) {
		Object.assign(this, opts);
		this.create_dialog();
	}

	create_dialog() {
		this.dialog = new frappe.ui.Dialog({
			title: __("Import Subscribers"),
			fields: this.get_fields(),
			primary_action: (data) => {
				data = this.process_data(data)
				frappe.call({
					method: "frappe.email.doctype.email_group.email_group.import_from",
					args: {
						"name": this.frm.doc.name,
						"doctype": data.doctype,
						"filters": data.filters,
						"auto_update": data.auto_update
					}
				}).then(r => {
					this.frm.refresh_fields();
				})

				this.dialog.hide();
			},
			primary_action_label: __("Import")
		});
		this.frm.doc.import_doctype && this.setup_filters(this.frm.doc.import_doctype)
		this.dialog.show();
	}

	get_fields() {
		return [
			{
				fieldtype:"Select",
				options: this.frm.doc.__onload.import_types,
				label:__("Import Email From"),
				fieldname:"doctype",
				default: this.frm.doc.import_doctype,
				reqd:1,
				onchange: () => {
					this.setup_filters(this.dialog.get_value("doctype"));
				}
			},
			{
				fieldtype: "HTML",
				fieldname: "filter_area_loading",
			},
			{
				fieldtype: "HTML",
				fieldname: "filter_area",
				hidden: 1,
			},
			{
				fieldtype: "Check",
				fieldname: "auto_update",
				label: __("Automatically update this email group"),
				default: this.frm.doc.auto_update
			}
		]
	}

	setup_filters(doctype) {
		if (this.filter_group) {
			this.filter_group.wrapper.empty();
			delete this.filter_group;
		}

		let $loading = this.dialog.get_field("filter_area_loading").$wrapper;
		$(`<span class="text-muted">${__("Loading Filters...")}</span>`).appendTo($loading);

		this.filters = []

		if (doctype == this.frm.doc.import_doctype) {
			const obj = JSON.parse(this.frm.doc.import_filters)
			this.filters = Object.keys(obj).length ? Object.keys(obj).map(f => {
				return [doctype, f, obj[f][0], obj[f][1]]
			}) : []
		}

		this.filter_group = new frappe.ui.FilterGroup({
			parent: this.dialog.get_field("filter_area").$wrapper,
			doctype: doctype,
			on_change: () => {},
		});

		this.filter_group.wrapper.find('.apply-filters').hide();

		frappe.model.with_doctype(doctype, () => {
			this.filter_group.add_filters_to_filter_group(this.filters);
			this.hide_field("filter_area_loading");
			this.show_field("filter_area");
		});
	}

	process_data(data) {
		let stats_filter = {};

		if (this.filter_group) {
			let filters = this.filter_group.get_filters();
			if (filters.length) {
				filters.forEach((arr) => {
					stats_filter[arr[1]] = [arr[2], arr[3]];
				});

				data.filters = JSON.stringify(stats_filter);
			}
		}

		return data;
	}

	hide_field(fieldname) {
		this.dialog.set_df_property(fieldname, "hidden", true);
	}

	show_field(fieldname) {
		this.dialog.set_df_property(fieldname, "hidden", false);
	}

}
