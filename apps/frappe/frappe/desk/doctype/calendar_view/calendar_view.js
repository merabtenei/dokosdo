// Copyright (c) 2017, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Calendar View', {
	onload: function(frm) {
		frm.trigger('reference_doctype');
	},
	refresh: function(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Show Calendar'),
				() => frappe.set_route('List', frm.doc.reference_doctype, 'Calendar', frm.doc.name));
		}
	},
	reference_doctype: function(frm) {
		const { reference_doctype } = frm.doc;
		if (!reference_doctype) return;

		frappe.model.with_doctype(reference_doctype, () => {
			const meta = frappe.get_meta(reference_doctype);

			const value_field_options = meta.fields.filter(
				df => !frappe.model.no_value_type.includes(df.fieldtype)
			).map(df => df.fieldname);

			const date_options = meta.fields.filter(
				df => ['Date', 'Datetime'].includes(df.fieldtype)
			).map(df => df.fieldname);

			const color_options = meta.fields.filter(
				df => ['Color'].includes(df.fieldtype)
			).map(df => df.fieldname);

			const check_options = meta.fields.filter(
				df => ['Check'].includes(df.fieldtype)
			).map(df => df.fieldname);

			const select_options = meta.fields.filter(
				df => ['Select'].includes(df.fieldtype)
			).map(df => df.fieldname);

			frm.set_df_property('subject_field', 'options', value_field_options);
			frm.set_df_property('start_date_field', 'options', date_options);
			frm.set_df_property('end_date_field', 'options', date_options);
			frm.set_df_property('all_day_field', 'options', check_options);
			frm.set_df_property('status_field', 'options', value_field_options);
			frm.set_df_property('color_field', 'options', color_options);
			frm.set_df_property('recurrence_rule_field', 'options', value_field_options);
			frm.set_df_property('secondary_status_field', 'options', select_options);
			frm.trigger("secondary_status_field");
			frm.refresh();
		});
	},
	secondary_status_field: function(frm) {
		if (frm.doc.secondary_status_field) {
			frappe.model.with_doctype(frm.doc.reference_doctype, () => {
				const meta = frappe.get_meta(frm.doc.reference_doctype);
				console.log(meta)
				frm.set_df_property('secondary_status', 'options', meta.fields.filter(f => f.fieldname == frm.doc.secondary_status_field)[0].options, frm.doc.name, "value");
			})
		}
	}
});