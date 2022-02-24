// Copyright (c) 2019, Dokos and Contributors
// MIT License. See license.txt

frappe.last_edited_letter = {};

frappe.views.LetterComposer = class LetterComposer {
	constructor(opts) {
		$.extend(this, opts);
		this.make();
	}

	make() {
		const me = this;

		this.dialog = new frappe.ui.Dialog({
			title: (this.title || __("New Letter")),
			no_submit_on_enter: true,
			fields: this.get_fields(),
			primary_action_label: __("Print a PDF"),
			primary_action: function() {
				me.delete_saved_draft();
				me.print_action();
				me.dialog.hide();
			}
		});

		this.prepare();
		this.dialog.show();
	}

	get_fields() {
		const fields= [
			{label:__("Email Template"), fieldtype:"Link", options:"Email Template",
				fieldname:"email_template"},
			{fieldtype: "Section Break"},
			{label:__("Title"), fieldtype:"Data", fieldname:"title"},
			{
				label:__("Message"),
				fieldtype:"Text Editor", reqd: 1,
				fieldname:"content",
				onchange: frappe.utils.debounce(this.save_as_draft.bind(this), 300)
			},
			{fieldtype: "Section Break"},
			{label:__("Attach to document"), fieldtype:"Check",
				fieldname:"attach_to_document", default: 1},
			{fieldtype: "Column Break"},
			{label:__("Letterhead"), fieldtype:"Link", options:"Letter Head",
				fieldname:"letter_head", default: this.frm.doc.letter_head},
		];

		return fields;
	}

	prepare() {
		this.setup_email_template();
	}

	setup_email_template() {
		const me = this;

		this.dialog.fields_dict["email_template"].df.onchange = () => {
			const email_template = me.dialog.fields_dict.email_template.get_value();

			if (email_template) {
				const prepend_reply = function(reply) {
					if(me.reply_added===email_template) {
						return;
					}
					const subject_field = me.dialog.fields_dict.title;
					const content_field = me.dialog.fields_dict.content;
					let subject = subject_field.get_value() || "";
					let content = content_field.get_value() || "";

					content = [reply.message, "<br>", content];
					content_field.set_value(content.join(''));
					subject_field.set_value(reply.subject);

					me.reply_added = email_template;
					me.title = reply.subject;
				}
	
				frappe.call({
					method: 'frappe.email.doctype.email_template.email_template.get_email_template',
					args: {
						template_name: email_template,
						doc: me.frm.doc
					},
					callback: function(r) {
						prepend_reply(r.message);
					},
				});
			}

		}
	}

	save_as_draft() {
		if (this.dialog) {
			try {
				let message = this.dialog.get_value('content');
				message = message.split(frappe.separator_element)[0];
				localStorage.setItem(this.frm.doctype + this.frm.docname, message);
			} catch (e) {
				// silently fail
				console.log(e);
				console.warn('[Communication] localStorage is full. Cannot save message as draft');
			}
		}
	}

	delete_saved_draft() {
		if (this.dialog) {
			try {
				localStorage.removeItem(this.frm.doctype + this.frm.docname);
			} catch (e) {
				console.log(e);
				console.warn('[Communication] Cannot delete localStorage item'); // eslint-disable-line
			}
		}
	}

	print_action() {
		const me = this;
		const content = this.dialog.fields_dict.content.get_value();
		const letter_head = this.dialog.fields_dict.letter_head.get_value();
		const title = this.dialog.fields_dict.title.get_value() || this.title;
		const attach = this.dialog.fields_dict.attach_to_document.get_value();

		let formData = new FormData();
		formData.append("html", content);
		formData.append("title", title || __("Letter"));
		formData.append("letterhead", letter_head || null);
		formData.append("attach", attach);
		formData.append("doctype", this.frm.doctype);
		formData.append("docname", this.frm.docname);

		let xhr = new XMLHttpRequest();
		xhr.open("POST", '/api/method/frappe.utils.print_format.letter_to_pdf');
		xhr.setRequestHeader("X-Frappe-CSRF-Token", frappe.csrf_token);
		xhr.responseType = "arraybuffer";
	
		xhr.onload = function(success) {
			if (this.status === 200) {
				let blob = new Blob([success.currentTarget.response], {type: "application/pdf"});
				let objectUrl = URL.createObjectURL(blob);
	
				//Open report in a new window
				let w = window.open(objectUrl);
				me.frm.sidebar.reload_docinfo();

				if(!w) {
					frappe.msgprint(__("Please enable pop-ups in your browser"))
				}
			}
		};
		xhr.send(formData);

	}
};