import TemplateFieldSelectorDialog from './TemplateFieldSelector.vue';

export default class TemplateFieldSelector {
	constructor(opts) {
		Object.assign(this, opts);
		this.make_dialog();

		frappe.field_selector_updates.on('done', () => {
			this.selector_area.$destroy();
		});
	}

	make_dialog() {
		this.dialog = new frappe.ui.Dialog({
			title: __("Select a field"),
			fields: [
				{
					label: __('Select a reference DocType'),
					fieldname: 'references',
					fieldtype: 'Link',
					options: 'DocType',
					default: this.default_doctype,
					onchange: () => {
						const value = this.dialog.fields_dict.references.value;
						this.default_doctype = value;
						if (value) {
							frappe.field_selector_updates.trigger('reference_update', value);
						}
					}
				},
				{
					fieldtype: 'HTML',
					fieldname: 'upload_area'
				}
			],
			primary_action_label: __('Add'),
			primary_action: () => {
				frappe.field_selector_updates.trigger('submit');
				this.dialog.hide();
			}
		});

		this.wrapper = this.dialog.fields_dict.upload_area.$wrapper[0];

		this.selector_area = new Vue({
			el: this.wrapper,
			render: h => h(TemplateFieldSelectorDialog, {
				props: { quill: this.quill, Quill: this.Quill, doctype: this.default_doctype }
			})
		});

		this.dialog.show();
	}
}

frappe.provide('frappe.field_selector_updates')
frappe.utils.make_event_emitter(frappe.field_selector_updates);