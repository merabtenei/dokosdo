from frappe import _


def get_data():
	return {
		'fieldname': 'auto_repeat',
		'transactions': [
			{
				'label': _('Logs'),
				'items': ['Auto Repeat Log']
			},
		]
	}