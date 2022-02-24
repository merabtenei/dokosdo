import Modules from './components/Modules.vue';

frappe.provide('frappe.modules');
frappe.provide('frappe.modules_dashboard')
frappe.utils.make_event_emitter(frappe.modules_dashboard);

frappe.modules.Home = class {
	constructor({ parent }) {
		this.$parent = $(parent);
		this.page = parent.page;
		this.setup_header();
		this.make_body();
	}
	make_body() {
		this.$modules_container = this.$parent.find('.layout-main');
		Vue.prototype.__ = window.__;
		Vue.prototype.frappe = window.frappe;
		new Vue({
			el: this.$modules_container[0],
			render: h => h(Modules)
		});
	}
	setup_header() {
		this.page.set_secondary_action(__("Edit Dashboard"), () => {
			this.edit_module()
		}, "octicon octicon-pencil").removeClass('btn-sm').addClass('btn-xs');
	}
	edit_module() {
		const fields = get_fields()
		const d = new frappe.ui.Dialog({
			title: __('Add a widget'),
			fields: fields,
			primary_action_label: __('Add'),
			primary_action: (values) => {
				const { widget_type, ...args } = values;
				frappe.xcall('frappe.desk.doctype.desk.desk.add_widget',
					{origin: frappe.get_route()[1], widget_type: values.widget_type, args})
				.then(() => frappe.modules_dashboard.trigger("widget_added"))
				d.hide();
			}
		});

		d.disable_primary_action()
		d.show();

		function get_fields() {
			return [
				{
					label: __("Widget type"),
					fieldname: "widget_type",
					fieldtype: 'MultiCheck',
					options: [
						{ label: __("Chart"), value: "Dashboard Chart" },
						{ label: __("Statistics"), value: "Dashboard Card" }
					],
					columns: 2,
					reqd: 1,
					on_change: function(value) {
						const widget_type = d.fields_dict.widget_type
						const checked = widget_type.get_checked_options()
						if (checked && checked.length > 1) {
							const index = widget_type.selected_options.indexOf(checked[0]);
							if(index > -1) {
								widget_type.selected_options.splice(index, 1);
							}
							widget_type.refresh_input();
						}
					}
				},
				{
					label: __("Chart"),
					fieldname: "chart",
					fieldtype: 'Link',
					options: "Dashboard Chart",
					depends_on: "eval:doc.widget_type=='Dashboard Chart'",
					onchange: () => {
						const value = d.fields_dict.chart.value;
						if (value) {
							check_total_width("Dashboard Chart", value);
						}
					}
				},
				{
					label: __("Card"),
					fieldname: "card",
					fieldtype: 'Link',
					options: "Dashboard Card",
					depends_on: "eval:doc.widget_type=='Dashboard Card'",
					onchange: () => {
						const value = d.fields_dict.card.value;
						if (value) {
							check_total_width("Dashboard Card", value);
						}
					}
				}
			]
		}

		function check_total_width(widget_type, value) {
			frappe.xcall('frappe.desk.doctype.desk.desk.check_widget_width', 
				{module: frappe.get_route()[1], widget_type: widget_type, value: value})
			.then((result) => { 
				result ? d.enable_primary_action() : d.disable_primary_action() 
			})
		}
	}
};
