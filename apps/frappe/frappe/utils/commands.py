def add_line_after(function):
	"""Adds an extra line to STDOUT after the execution of a function this decorates"""
	def empty_line(*args, **kwargs):
		result = function(*args, **kwargs)
		print()
		return result
	return empty_line


def log(message, colour=''):
	"""Coloured log outputs to STDOUT"""
	colours = {
		"nc": '\033[0m',
		"blue": '\033[94m',
		"green": '\033[92m',
		"yellow": '\033[93m',
		"red": '\033[91m',
		"silver": '\033[90m'
	}
	colour = colours.get(colour, "")
	end_line = '\033[0m'
	print(colour + message + end_line)