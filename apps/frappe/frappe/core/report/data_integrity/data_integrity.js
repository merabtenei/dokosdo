// Copyright (c) 2019, Dokos and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Data Integrity"] = {
	"filters": [
		{
			"fieldname":"doctype",
			"label": __("DocType"),
			"fieldtype": "Link",
			"options": "DocType",
			"reqd": 1,
			"get_query": function () {
				return {
					"query": "frappe.core.report.data_integrity.data_integrity.query_doctypes"
				}
			}
		}
	],
	"formatter": function(value, row, column, data, default_formatter) {

		if (column.fieldname == "comments") {
			const icon = (data.icon=="success") ? "fa-check": (data.icon=="warning") ? "fa-bell" : "fa-exclamation"
			const color = (data.icon=="success") ? "green": (data.icon=="warning") ? "orange" : "red"
			return `<div class="text-left">
						<i class="fa ${icon}" style="color: ${color};"></i>
						${value}
					</div>`;
		}
		return value;
	}
}
