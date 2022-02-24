import WebFormList from './web_form_list'
import WebForm from './web_form'

frappe.ready(function() {
	let query_params = frappe.utils.get_query_params();
	let wrapper = $(".web-form-wrapper");
	let is_list = parseInt(wrapper.data('is-list')) || query_params.is_list;
	let webform_doctype = wrapper.data('web-form-doctype');
	let webform_name = wrapper.data('web-form');
	let login_required = parseInt(wrapper.data('login-required'));
	let allow_delete = parseInt(wrapper.data('allow-delete'));
	const allow_edit = parseInt(wrapper.data('allow-edit'));
	let doc_name = query_params.name || '';
	let is_new = query_params.new;

	if (login_required) show_login_prompt();
	else if (is_list) show_grid();
	else show_form(webform_doctype, webform_name, is_new);

	document.querySelector("body").style.display = "flex";

	function show_login_prompt() {
		const login_required = new frappe.ui.Dialog({
			title: __("Not Permitted"),
			primary_action_label: __("Login"),
			primary_action: () => {
				window.location.replace('/login?redirect-to=' + window.location.pathname);
			}
		});
		login_required.set_message(__("You are not permitted to access this page."));
		login_required.show();
	}

	function show_grid() {
		new WebFormList({
			parent: wrapper,
			doctype: webform_doctype,
			web_form_name: webform_name,
			settings: {
				allow_delete
			}
		});
	}

	function show_form() {
		let web_form = new WebForm({
			parent: wrapper,
			is_new,
			web_form_name: webform_name,
			allow_edit
		});

		get_data().then(r => {
			const data = setup_fields(r.message);
			let web_form_doc = data.web_form;
			let doc = r.message.doc || build_doc(r.message);
			web_form.prepare(web_form_doc, doc ? doc : {});
			web_form.make();
			web_form.set_default_values();
		})

		function build_doc(form_data) {
			let doc = {};
			form_data.web_form.web_form_fields.forEach(df => {
				if (df.default) {
					return doc[df.fieldname] = df.default;
				}
			});
			return doc;
		}

		function get_data() {
			return frappe.call({
				method: "frappe.website.doctype.web_form.web_form.get_form_data",
				args: {
					doctype: webform_doctype,
					docname: doc_name,
					web_form_name: webform_name
				},
				freeze: true
			});
		}

		function setup_fields(form_data) {
			form_data.web_form.web_form_fields.map(df => {
				df.is_web_form = true;
				if (df.fieldtype === "Table") {
					df.get_data = () => {
						let data = [];
						if (form_data.doc) {
							data = form_data.doc[df.fieldname];
						}
						return data;
					};

					df.fields = form_data[df.fieldname];
					$.each(df.fields || [], function(_i, field) {
						if (field.fieldtype === "Link") {
							field.only_select = true;
						}
						field.is_web_form = true;
						field.read_only = df.read_only ? df.read_only : (!is_new && !allow_edit);
					});

					if (df.fieldtype === "Attach") {
						df.is_private = true;
					}

					df.read_only = df.read_only ? df.read_only : (!is_new && !allow_edit);

					delete df.parent;
					delete df.parentfield;
					delete df.parenttype;
					delete df.doctype;

					return df;
				}
				if (df.fieldtype === "Link") {
					df.only_select = true;
				}
				if (["Attach", "Attach Image"].includes(df.fieldtype)) {
					if (typeof df.options !== "object") {
						df.options = {};
					}
					df.options.disable_file_browser = true;
				}

				df.read_only = df.read_only ? df.read_only : (!is_new && !allow_edit);
			});

			return form_data;
		}
	}
});
