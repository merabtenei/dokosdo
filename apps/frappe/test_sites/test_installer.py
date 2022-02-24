import os
import frappe
import json

from frappe.installer import _new_site
import frappe.build

def get_site_config(site_name):
	site_config = None
	with open('sites/{site_name}/site_config.json'.format(site_name=site_name)) as site_config_file:
		site_config = json.load(site_config_file)
	return site_config

def main():
	site_name = 'test_site'
	site_config = get_site_config(site_name)

	db_type = 'mariadb'
	db_port = site_config.get('db_port', 3306)
	db_host = site_config.get('db_host')
	mariadb_root_username = 'root'
	mariadb_root_password = 'test_dodock'

	frappe.init(site_name, sites_path="sites", new_site=True)

	_new_site(
		None,
		site_name,
		mariadb_root_username=mariadb_root_username,
		mariadb_root_password=mariadb_root_password,
		admin_password='admin',
		verbose=True,
		source_sql=None,
		force=True,
		db_type=db_type,
		reinstall=True,
		db_host=db_host,
		db_port=db_port,
		install_apps=[]
	)

	if frappe.redis_server:
		frappe.redis_server.connection_pool.disconnect()

	frappe.build.bundle(True)

	exit(0)


if __name__ == "__main__":
	main()
