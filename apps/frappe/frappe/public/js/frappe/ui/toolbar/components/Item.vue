<template>
	<div
		class="dodock-sidebar-item"
		@mouseenter="mouseEnter($event)"
		@touchend="touchEnd($event)"
		@click="itemClick"
	>
		<a
			class="dodock-sidebar-link"
			:href="'/app/' + frappe.router.slug(item.name)"
		>
			<i class="dodock-sidebar-icon"
				:style="{
					//backgroundColor: getBackgroundColor(item.icon),
					//'--icon-stroke': getBackgroundColor(item.icon)
					'--icon-fill': getBackgroundColor(item.icon)
				}"
				v-html="frappe.utils.icon(item.icon || 'folder-open', 'lg')">
			</i>
			<template v-if="!isCollapsed">
				<span class="dodock-sidebar-title">{{ item.label }}</span>
			</template>
		</a>
	</div>
</template>

<script>
export default {
	props: {
		item: {
			type: Object,
			required: true
		},
		isCollapsed: {
			type: Boolean
		}
	},
	methods: {
		mouseEnter(event) {
			if (this.isCollapsed) {
				this.$parent.$emit('mouseEnterItem', {
					item: this.item,
					pos:
						event.currentTarget.getBoundingClientRect().top -
						this.$parent.$el.getBoundingClientRect().top,
						height: this.$el.offsetHeight
				})
			}
		},
		touchEnd(event) {
			if (this.isCollapsed) {
				this.$parent.$emit('touchEndItem')
			}
		},
		itemClick() {
			this.$emit('itemClick');
		},
		getBackgroundColor(icon) {
			const colorMap = {
				accounting: "#407395",
				assets: "#457b9d",
				tool: "#e9c46a",
				buying: "#e76f51",
				crm: "#ec9a9a",
				hr: "#457b9d",
				loan: "#e96a70",
				"money-coins-1": "#15aabf",
				project: "#BF90D4",
				quality: "#1abc9c",
				sell: "#2a9d8f",
				support: "#72ac82",
				website: "#84b7c5",
				settings: "#aec8ff",
				customization: "#F8A787",
				integration: "#35abb7",
				users: "#e8525b",
				organization: "#c2831c",
				retail: "#62B6CB",
				stock: "#f4a261",
				map: "#eeb867",
				agriculture : "#ffcb61"
			}
			return colorMap[icon] || "var(--primary-color)"
		}
	}
}
</script>
