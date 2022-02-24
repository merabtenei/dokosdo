<template>
	<div>
		<div
		class="v-sidebar-menu hidden-sm hidden-xs"
		:class="[!isCollapsed ? 'dodock-sidebar-default' : 'dodock-sidebar-collapsed']"
		:style="[{'width': sidebarWidth}, mobileDisplay ? {'display': 'block !important'} : '', !showBottomButton ? {'padding-bottom': '20px'} : '']"
		@mouseenter="mouseEnter"
		@mouseleave="mouseLeave"
		@wheel="onWheel"
		@scroll="onWheel"
		>
		<div class="dodock-sidebar-list" id="sidebard-modules-list" ref="sidebarList">
			<template v-for="(mod, mod_index) in moduleCategories">
			<div
				v-if="modules[mod]&&modules[mod].length&&mod!='Modules'"
				class="dodock-sidebar-divider"
				:class="[!isCollapsed ? '' : 'collapsed']"
				:key="mod + mod_index"
			>
				<span>{{ __(mod) }}</span>
			</div>
			<template v-for="(item, index) in modules[mod]">
				<item
				:key="item.name + index"
				:item="item"
				:is-collapsed="isCollapsed"
				@itemClick="itemClick"
				/>
			</template>
			</template>
		</div>
		<button
			v-if="!mobileDisplay && showBottomButton"
			class="collapse-btn"
			:class="goToTop ? 'up-btn' : 'down-btn'"
			@click="scrollUpDown"
		/>
		</div>
	</div>
</template>

<script>
	import Item from "./Item.vue";
	export default {
	name: "SidebarMenu",
	components: {
		Item
	},
	data() {
		return {
		isCollapsed: true,
		modules: {},
		modules_list: [],
		width: "200px",
		widthCollapsed: "50px",
		mobileDisplay: false,
		goToTop: false,
		isMounted: false,
		timer: null,
		moduleCategories: ["Modules", "Administration"]
		};
	},
	created() {
		frappe.sidebar_update.on("toggle_mobile_menu", () => {
		this.mobileDisplay ? this.mobileCollapse() : this.mobileExpand();
		});
	},
	computed: {
		sidebarWidth() {
		return this.mobileDisplay
			? "100%"
			: this.isCollapsed
			? this.widthCollapsed
			: this.width;
		},
		showBottomButton() {
		if (this.isMounted) {
			return (
			this.modules_list.length * 50 >
			this.$refs.sidebarList.clientHeight - 35
			);
		}
		}
	},
	mounted() {
		this.isMounted = true;
		this.getModules();
	},
	methods: {
		mouseLeave() {
			this.isCollapsed = this.mobileDisplay ? false : true;
		},
		mouseEnter() {
			this.isCollapsed = false;
		},
		mobileExpand() {
			this.isCollapsed = false;
			this.mobileDisplay = true;
		},
		mobileCollapse() {
			this.mobileDisplay = false;
		},
		getModules() {
			frappe.xcall("frappe.desk.desktop.get_desk_sidebar_items").then(r => {
				this.modules_list = r;
				this.modules = {
					"Modules": this.modules_list.filter(f => f.category == "Modules"),
					"Administration": this.modules_list.filter(f => f.category == "Administration")
				}

				const maxLength = this.modules_list.reduce((acc, item) => {
					return item.label.length > acc ? item.label.length : acc;
				}, 0);

				this.width =
				Math.max(maxLength > 25 ? maxLength * 10 : maxLength * 12, 200) + "px";
			});
		},
		scrollUpDown() {
			const scrollHeight = document.querySelector("#sidebard-modules-list")
				.scrollHeight;
			this.onWheel(
				{
				deltaY: this.goToTop ? -scrollHeight : scrollHeight
				},
				true
			);
			this.goToTop = !this.goToTop;
		},
		onWheel(e, smooth = false) {
			const list = this.$el.querySelector("#sidebard-modules-list");
			smooth
				? list.scrollBy({ top: e.deltaY, left: 0, behavior: "smooth" })
				: list.scrollBy(0, e.deltaY);

			this.measureScroll();
		},
		measureScroll() {
			const list = this.$el.querySelector("#sidebard-modules-list");
			if (list.clientHeight + list.scrollTop >= list.scrollHeight) {
				this.goToTop = true;
			} else {
				this.goToTop = false;
			}
		},
		itemClick() {
			this.mobileDisplay && (this.mobileDisplay = !this.mobileDisplay);
		}
	}
};
</script>

<style lang="scss">
@import "./sidebar.scss";
</style>