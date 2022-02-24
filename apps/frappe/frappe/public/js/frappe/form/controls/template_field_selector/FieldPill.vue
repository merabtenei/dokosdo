<template>
	<div class="badge align-middle align-text-top align-text-bottom" :class="pillStyle" v-on:click="clicked">
		{{label}}
	</div>
</template>
<script>
export default {
	name: "card",
	props: {
		label: String,
		fieldname: String,
		fieldtype: String,
		parent: String,
		reference: String,
		function: String,
		selectedPills: Array
	},
	data() {
		return {
			selected: false
		}
	},
	computed: {
		pillStyle() {
			return (this.selected === true) ? "selectable-badge" : ""
		}
	},
	methods: {
		clicked() {
			this.selected = !this.selected;

			if (this.selected === true){
				this.selectedPills.push({
					fieldname: this.fieldname,
					label: this.label,
					fieldtype: this.fieldtype,
					parent: this.parent,
					reference: this.reference,
					function: this.function
				})
			} else {
				const removeIndex = this.selectedPills.map(function(item) { return item.fieldname; }).indexOf(this.fieldname);
				this.selectedPills.splice(removeIndex, 1);
			}
		}
	}
};
</script>
<style>
.badge {
	cursor: pointer;
}

.selectable-badge {
	background-color: #6195FF;
	color: #fff;
}

</style>