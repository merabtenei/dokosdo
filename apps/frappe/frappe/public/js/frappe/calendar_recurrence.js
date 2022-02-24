import { RRule, ENGLISH } from '../lib/rrule/rrule-tz.min.js';

// 'en' is implied, don't add it to this array
const availableLanguages = ['fr']
frappe.CalendarRecurrence = class {
	constructor(opts) {
		Object.assign(this, opts)
		this.currentRule = {}
		this.start_day = moment(this.start_field ? this.frm.doc[this.start_field] : this.frm.doc.starts_on)

		if (availableLanguages.includes(frappe.boot.lang)) {
			frappe.require(`/assets/frappe/js/lib/rrule/locales/${frappe.boot.lang}.js`, () => {
				this.recurrence_process()
			})
		} else {
			this.recurrence_process()
		}
	}

	recurrence_process() {
		this.parse_rrule()
		this.make()
		if (this.show) {
			this.dialog.show()
		} else {
			this.set_repeat_text(this.get_current_rrule())
		}
	}

	parse_rrule() {
		if (this.frm.doc.rrule) {
			const rule = RRule.fromString(this.frm.doc.rrule)
			this.currentRule = rule.origOptions
		}
	}

	get_current_rrule() {
		return new RRule(this.currentRule)
	}

	gettext(id) {
		if (availableLanguages.includes(frappe.boot.lang) && (typeof RRULE_STRINGS !== 'undefined')){
			return RRULE_STRINGS[id] || id;
		}
		return id
	}

	frequency_map() {
		return {
			'daily': RRule.DAILY,
			'weekly': RRule.WEEKLY,
			'monthly': RRule.MONTHLY,
			'yearly': RRule.YEARLY
		}
	}

	get_frequency(value) {
		const map = this.frequency_map()
		return map[value];
	}

	get_default_frequency(value) {
		const map = dict_reverse(this.frequency_map())
		return map[value];
	}

	weekday_map() {
		return {
			'monday': RRule.MO,
			'tuesday': RRule.TU,
			'wednesday': RRule.WE,
			'thursday': RRule.TH,
			'friday': RRule.FR,
			'saturday': RRule.SA,
			'sunday': RRule.SU
		}
	}

	get_by_weekday(values) {
		const map = this.weekday_map()

		const result = Object.keys(map)
		.filter(day => values[day] === 1)
		.map(day => map[day])
		return result
	}

	get_default_by_weekday(day) {
		const map = this.weekday_map()
		if (this.currentRule.byweekday && this.currentRule.byweekday.length) {
			const selectedDays = this.currentRule.byweekday.map(v => v.weekday)
			return selectedDays.includes(map[day].weekday) ? 1 : 0
		}
		return 0;
	}

	get_by_day_label() {
		const date_day = this.start_day.date()
		return __("Monthly on day {}", [date_day])
	}

	get_by_pos_label() {
		const ordinals = ["", __("first"), __("second"), __("third"), __("fourth"), __("fifth")];
		const occurence = ordinals[this.get_by_pos_count()]
		return __("Monthly on the {0} {1}", [occurence, __(this.start_day.format("dddd"))])
	}

	get_by_pos_count() {
		return Math.ceil(this.start_day.date()/7)
	}

	make() {
		const me = this;
		this.dialog = new frappe.ui.Dialog({
			title: __('Recurrence'),
			fields: [
				{
					fieldname: "freq",
					label: __("Frequency"),
					fieldtype: "Select",
					options: [
						{label: __('Daily'), value: 'daily'},
						{label: __('Weekly'), value: 'weekly'},
						{label: __('Monthly'), value: 'monthly'},
						{label: __('Yearly'), value: 'yearly'}
					]
				},
				{
					fieldname: "until",
					label: __("Repeat until"),
					fieldtype: "Date"
				},
				{
					fieldname: "interval",
					label: __("Frequency interval"),
					fieldtype: "Int",
					default: 1
				},
				{
					fieldname: "day_col",
					fieldtype: "Column Break"
				},
				{
					fieldname: "monthly_options",
					label: __("Options"),
					fieldtype: "Select",
					depends_on: "eval:doc.freq=='monthly'",
					options: [
						{label: me.get_by_day_label(), value: 'by_day'},
						{label: me.get_by_pos_label(), value: 'by_pos'},
					],
					default: 'by_day'
				},
				{
					fieldname: "monday",
					label: __("Monday"),
					fieldtype: "Check",
					depends_on: "eval:doc.freq=='weekly'",
					default: me.get_default_by_weekday("monday")
				},
				{
					fieldname: "tuesday",
					label: __("Tuesday"),
					fieldtype: "Check",
					depends_on: "eval:doc.freq=='weekly'",
					default: me.get_default_by_weekday("tuesday")
				},
				{
					fieldname: "wednesday",
					label: __("Wednesday"),
					fieldtype: "Check",
					depends_on: "eval:doc.freq=='weekly'",
					default: me.get_default_by_weekday("wednesday")
				},
				{
					fieldname: "thursday",
					label: __("Thursday"),
					fieldtype: "Check",
					depends_on: "eval:doc.freq=='weekly'",
					default: me.get_default_by_weekday("thursday")
				},
				{
					fieldname: "friday",
					label: __("Friday"),
					fieldtype: "Check",
					depends_on: "eval:doc.freq=='weekly'",
					default: me.get_default_by_weekday("friday")
				},
				{
					fieldname: "saturday",
					label: __("Saturday"),
					fieldtype: "Check",
					depends_on: "eval:doc.freq=='weekly'",
					default: me.get_default_by_weekday("saturday")
				},
				{
					fieldname: "sunday",
					label: __("Sunday"),
					fieldtype: "Check",
					depends_on: "eval:doc.freq=='weekly'",
					default: me.get_default_by_weekday("sunday")
				}
			],
			primary_action_label: __('Save'),
			primary_action:(values) => {
				this.frm.doc.repeat_till = null;
				const rule_obj = {
					freq: me.get_frequency(values.freq),
					interval: values.interval || 1
				}

				const weekdays_values = me.get_by_weekday(values)
				if (weekdays_values && weekdays_values.length) {
					Object.assign(rule_obj, {byweekday: weekdays_values})
				}

				if (values.until) {
					Object.assign(rule_obj, {until: moment.utc(values.until).toDate()})
					this.frm.doc.repeat_till = moment(values.until).format('YYYY-MM-DD');
				}

				if (values.freq == 'monthly' && values.monthly_options) {
					if (values.monthly_options == "by_day") {
						Object.assign(rule_obj, {bymonthday: [moment(me.start_day).date()]})
					} else {
						const weekday_map = me.weekday_map()
						Object.assign(rule_obj, {
							byweekday: weekday_map[me.start_day.format("dddd").toLowerCase()],
							bysetpos: [me.get_by_pos_count()]
						})
					}
				}

				const rule = new RRule(rule_obj)
				this.frm.doc.rrule = rule.toString()
				this.set_repeat_text(rule)
				this.dialog.hide()
				this.frm.refresh_fields("repeat")
			}
		})
		this.init_dialog()
	}

	set_repeat_text(rule) {
		$(this.frm.fields_dict['repeat'].wrapper).html(`<p>${this.get_repeat_text(rule)}</p>`);
	}

	get_repeat_text(rule) {
		const me = this;
		return rule.toText(id => {
			return me.gettext(id);
		}, (typeof RRULE_DATES === 'undefined') ? ENGLISH : RRULE_DATES)
	}

	init_dialog() {
		const me = this;
		const field_default_values = {
			'freq': me.get_default_frequency(me.currentRule.freq),
			'until': me.currentRule.until ? moment(me.currentRule.until).format('YYYY-MM-DD') : null,
			'interval': me.currentRule.interval || 1,
			'monday': me.get_default_by_weekday("monday"),
			'tuesday': me.get_default_by_weekday("tuesday"),
			'wednesday': me.get_default_by_weekday("wednesday"),
			'thursday': me.get_default_by_weekday("thursday"),
			'friday': me.get_default_by_weekday("friday"),
			'saturday': me.get_default_by_weekday("saturday"),
			'sunday': me.get_default_by_weekday("sunday"),
			'monthly_options': me.currentRule.bysetpos ? 'by_pos' : 'by_day'
		}
		this.dialog.set_values(field_default_values);
	}
}

function dict_reverse(obj) {
	const new_obj = {}
	const rev_obj = Object.keys(obj).reverse();
	rev_obj.forEach(function(i, j) { 
		new_obj[obj[i]] = i;
	})
	return new_obj;
}