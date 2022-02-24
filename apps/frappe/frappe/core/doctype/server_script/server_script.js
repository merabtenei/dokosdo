// Copyright (c) 2019, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('Server Script', {
	refresh: function(frm) {
		if (frm.doc.script_type != 'Scheduler Event') {
			frm.dashboard.hide();
		}
	}
});
