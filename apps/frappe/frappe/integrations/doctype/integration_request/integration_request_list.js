frappe.listview_settings['Integration Request'] = {
	get_indicator: function(doc) {
		if (doc.status == "Autorized") {
			return [__("Autorized"), "blue", "status,=,Autorized"];
		} else if (doc.status == "Pending") {
			return [__("Pending"), "blue", "status,=,Pending"];
		} else if (doc.status == "Completed") {
			return [__("Completed"), "green", "status,=,Completed"];
		} else if (doc.status == "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		} else if (doc.status == "Failed") {
			return [__("Failed"), "orange", "status,=,Failed"];
		} else if (doc.status == "Not Handled") {
			return [__("Not Handled"), "gray", "status,=,Not Handled"];
		} else {
			return [__("Queued"), "darkgray", "status,=,Queued"];
		}
	}
};
