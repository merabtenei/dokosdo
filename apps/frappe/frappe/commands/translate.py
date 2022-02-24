from __future__ import unicode_literals, absolute_import, print_function
import click
from frappe.commands import pass_context, get_site
from frappe.exceptions import SiteNotSpecifiedError

APP_MAPPING = {"dokos": "erpnext", "dodock": "frappe"}

# translation
@click.command('build-message-files')
@pass_context
def build_message_files(context):
	"Build message files for translation"
	import frappe.translate
	for site in context.sites:
		try:
			frappe.init(site=site)
			frappe.connect()
			frappe.translate.rebuild_all_translation_files()
		finally:
			frappe.destroy()
	if not context.sites:
		raise SiteNotSpecifiedError

@click.command('new-language') #, help="Create lang-code.csv for given app")
@pass_context
@click.argument('lang_code') #, help="Language code eg. en")
@click.argument('app') #, help="App name eg. frappe")
def new_language(context, lang_code, app):
	"""Create lang-code.csv for given app"""
	import frappe.translate

	if not context['sites']:
		raise Exception('--site is required')

	# init site
	frappe.connect(site=context['sites'][0])
	translations = frappe.translate.get_untranslated(lang_code, get_all=all, app=APP_MAPPING.get(app, app), write=False)
	frappe.translate.write_translations_file(APP_MAPPING.get(app, app), lang_code, translations)

	print("File created at ./apps/{app}/{app}/translations/{lang_code}.json".format(app=APP_MAPPING.get(app, app), lang_code=lang_code))
	print("You will need to add the language in frappe/geo/languages.json, if you haven't done it already.")

@click.command('get-untranslated')
@click.argument('lang')
@click.argument('untranslated_file')
@click.option('--all', default=False, is_flag=True, help='Get all message strings')
@click.option('--app', default=None, help='Selected application')
@pass_context
def get_untranslated(context, lang, untranslated_file, all=None, app=None):
	"Get untranslated strings for language"
	import frappe.translate
	site = get_site(context)
	try:
		frappe.init(site=site)
		frappe.connect()
		frappe.translate.get_untranslated(lang, untranslated_file, get_all=all, app=APP_MAPPING.get(app, app))
	finally:
		frappe.destroy()

@click.command('update-translations')
@click.argument('lang')
@click.argument('translated-file')
@click.argument('app')
@pass_context
def update_translations(context, lang, translated_file, app):
	"Update translated strings"
	import frappe.translate
	site = get_site(context)
	try:
		frappe.init(site=site)
		frappe.connect()
		frappe.translate.update_translations(lang, translated_file, APP_MAPPING.get(app, app))
	finally:
		frappe.destroy()

@click.command('cleanup-translations')
@click.option('--app', 'apps', type=(str), multiple=True)
@click.option('--lang', 'langs', type=(str), multiple=True)
@pass_context
def cleanup_translations(context, apps=None, langs=None):
	"Cleanup translation files"
	import frappe.translate
	site = get_site(context)
	try:
		frappe.init(site=site)
		frappe.connect()
		frappe.translate.cleanup_translation_files([a.translate(APP_MAPPING) for a in apps], langs)
	finally:
		frappe.destroy()

@click.command('import-translations')
@pass_context
def import_translations():
	"""
		Deprecated
	"""
	click.echo("""
		import-translations is deprecated.
		You can use update-translations instead.
		""")

commands = [
	build_message_files,
	get_untranslated,
	import_translations,
	new_language,
	update_translations,
	cleanup_translations
]
