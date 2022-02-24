frappe.provide('frappe.ui.misc');
frappe.ui.misc.about = function() {
	if(!frappe.ui.misc.about_dialog) {
		var d = new frappe.ui.Dialog({title: __("Your application") });

		$(d.body).html(`<div>\
		<p>${__("Open Source Applications for the Web")}</p>
		<p><i class='uil uil-globe'></i>
			${ __("Website:") } <a href='https://dokos.io' target='_blank'>https://dokos.io</a></p>
		<p><i class='fab fa-github fa-fw'></i>
			${ __("Source:") } <a href='https://gitlab.com/dokos' target='_blank'>https://gitlab.com/dokos</a></p>
		<p><i class='fab fa-linkedin fa-fw'></i>\
			Linkedin: <a href='https://www.linkedin.com/company/dokos.io' target='_blank'>https://www.linkedin.com/company/dokos.io</a></p>\
		<p><i class='fab fa-twitter fa-fw'></i>\
			Twitter: <a href='https://twitter.com/dokos_io' target='_blank'>https://twitter.com/dokos_io</a></p>\
		<hr>
		<h4>${ __("Installed Apps") }</h4>
		<div id='about-app-versions'>${ __("Loading versions...") }</div>
		<hr>\
		<p class='text-muted'>&copy; ${ __("Dokos SAS and contributors")}</p>
		</div>`);

		frappe.ui.misc.about_dialog = d;

		frappe.ui.misc.about_dialog.on_page_show = function() {
			if(!frappe.versions) {
				frappe.call({
					method: "frappe.utils.change_log.get_versions",
					callback: function(r) {
						show_versions(r.message);
					}
				})
			} else {
				show_versions(frappe.versions);
			}
		};

		var show_versions = function(versions) {
			var $wrap = $("#about-app-versions").empty();
			$.each(Object.keys(versions).sort(), function(i, key) {
				var v = versions[key];
				if(v.branch) {
					var text = $.format('<p><b>{0}:</b> v{1} ({2})<br></p>',
						[v.title, v.branch_version || v.version, v.branch])
				} else {
					var text = $.format('<p><b>{0}:</b> v{1}<br></p>',
						[v.title, v.version])
				}
				$(text).appendTo($wrap);
			});

			frappe.versions = versions;
		}

	}

	frappe.ui.misc.about_dialog.show();

}
