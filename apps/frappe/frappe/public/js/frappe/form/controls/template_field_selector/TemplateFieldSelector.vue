<template>
	<div>
		<div class="field-pill-section-wrapper" v-for="field in Object.keys(fields)" :key="field">
			<div class="field-pill-title">
				<h4>
					<span v-if="showReference(field)" class="text-muted">{{ __("Reference Document : ") }}</span>
					<span v-else-if="field!==__('Custom Functions')" class="text-muted">{{ __("Linked Document : ") }}</span>
					{{ __(fields[field][0]["parent"]) }}
					<span v-if="'reference_label' in fields[field][0] && field!==__('Custom Functions')" class="text-muted">({{ __("Field") }}
						<i>{{ __(fields[field][0]["reference_label"]) }})</i>
					</span>
				</h4>
			</div>
			<div class="flex flex-wrap border rounded field-pill-section">
				<div class="field-pill-wrapper" v-for="f in fields[field]" :key="f.fieldname">
					<field-pill
					:label="f.label"
					:fieldname="f.fieldname"
					:fieldtype="f.fieldtype"
					:parent="f.parent"
					:reference="f.reference"
					:function="f.function"
					:selectedPills="selectedPills"
					>
					</field-pill>
			</div>
			</div>
		</div>
	</div>
</template>

<script>

import FieldPill from './FieldPill.vue'

export default {
	name: 'TemplateFieldSelectorDialog',
	components: {
		FieldPill
	},
	props: {
		quill: {
			default: null
		},
		Quill: {
			default: null
		},
		doctype: {
			default: null
		}
	},
	data() {
		return {
			fields: {},
			selectedPills: [],
			referenceDoc: null
		}
	},
	created() {
		frappe.field_selector_updates.on('reference_update', (reference) => {
			this.selectedPills = []
			this.get_fields(reference)
		})

		frappe.field_selector_updates.on('submit', () => {
			this.add_field_to_text();
			frappe.field_selector_updates.trigger('done');
		})
	},
	mounted() {
		if (this.doctype) {
			this.referenceDoc = this.doctype;
			this.get_fields(this.doctype)
		}
	},
	methods: {
		get_fields(reference) {
			this.referenceDoc = reference;
			frappe.xcall('frappe.email.doctype.email_template.email_template.get_template_fields', {reference: reference})
			.then(e => {
				this.fields = e
			})
		},
		add_field_to_text() {
			let range = this.quill.getSelection(true);

			this.selectedPills.forEach(value => {
				this.quill.insertEmbed(
					range.index,
					'template-blot',
					{
						parent: value.parent,
						fieldname: value.fieldname,
						label: value.label,
						reference: value.reference,
						label: value.label,
						function: value.function,
						fieldtype: value.fieldtype
					}
				);

				//Add a space after the marker and take the cursor to the inserted blot
				this.quill.insertText(range.index + 1, ' ', this.Quill.sources.USER);
				this.quill.setSelection(range.index + 2, this.Quill.sources.SILENT);
				})
		},
		showReference(field) {
			return field=="name" ? true : false
		}
	}
}

</script>

<style>

.field-pill-wrapper {
	margin: 5px;
}

.field-pill-section {
	padding: 5px 0;
}

.field-pill-title {
	padding-left: 10px;
}

.field-pill-section-wrapper {
	margin-top: 30px;
}

</style>