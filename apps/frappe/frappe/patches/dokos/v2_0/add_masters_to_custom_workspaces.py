import frappe

def execute():
	workspaces = frappe.get_all("Workspace", filters={
		"for_user": ("is", "set"),
	})

	for workspace in workspaces:
		doc = frappe.get_doc("Workspace", workspace.name)
		if not doc.links:
			extended_doc = frappe.get_doc("Workspace", doc.extends)
			for link in extended_doc.links:
				doc.append('links', {
					"type": link.type,
					"label": link.label,
					"link_type": link.link_type,
					"link_to": link.link_to,
					"dependencies": link.dependencies,
					"only_for": link.only_for,
					"onboard": link.onboard
				})

		doc.flags.ignore_links = True
		doc.save()