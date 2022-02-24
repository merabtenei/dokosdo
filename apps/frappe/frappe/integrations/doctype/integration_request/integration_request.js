// Copyright (c) 2016, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Integration Request', {
	refresh: function(frm) {
		frm.page.clear_actions_menu();
		if(frm.doc.status !== 'Completed'){
			frm.page.add_action_item(
				__('Set status as Completed'),
				() => {
					frappe.db.set_value(frm.doctype, frm.doc.name, "status", "Completed", r => {
						frm.reload_doc()
					})
				}
			);

			if(frm.doc.integration_type === 'Webhook') {
				frm.page.add_action_item(
					__('Retry processing the webhook'),
					() => {
						frappe.call({method: "retry_webhook", doc: frm.doc})
						.then(r => {
							frappe.show_alert({message:__("Processing in progress"), indicator:'green'});
							frm.reload_doc()
						})
					}
				);
			}
		} else {
			if(frm.doc.integration_type === 'Webhook') {
				frm.page.add_action_item(
					__('Reset the webhook'),
					() => {
						frm.set_value("status", "Queued")
						frm.set_value("reference_doctype", "")
						frm.set_value("reference_docname", "")
						frm.set_value("error", "")
						frm.save()
					}
				);
			}
		}

	}
});
