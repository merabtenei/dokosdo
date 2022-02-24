frappe.provide('frappe.views');

frappe.views.MapView = class MapView extends frappe.views.ListView {
	get view_name() {
		// __("Map")
		return 'Map';
	}

	setup_defaults() {
		super.setup_defaults();
		this.page_title = __('{0} Map', [this.page_title]);
	}

	get_fields() {
		this.gelocation_fields = this.meta.fields.filter(f => f.fieldtype === "Geolocation").map(f => f.fieldname)
		this.gelocation_fields.forEach(fieldname => {
			this.fields.push([fieldname, this.doctype]);
		})
		return super.get_fields();
	}

	get_list_fields() {
		this.list_fields = this.meta.fields
			.filter(f => (f.in_list_view === 1 || f.in_preview === 1))
			.reduce((prev, curr) => {
				return Object.assign(prev, {[curr.fieldname] : curr.label})
			}, {})
	}

	setup_view() {
		this.sort_selector.wrapper.hide();
		this.list_sidebar&&this.list_sidebar.parent.find(".list-tag-preview").hide();
	}

	prepare_data(data) {
		super.prepare_data(data);
		this.get_list_fields()
	}

	render() {
		this.make_wrapper();
		this.bind_leaflet_map();
		this.bind_leaflet_draw_control();
		this.render_map();
	}

	make_wrapper() {
		this.$result.empty();

		this.map_id = frappe.dom.get_unique_id();
		this.map_area = $(
			`<div class="map-wrapper border">
				<div id=${this.map_id} style="min-height: calc(100vh - 284px); z-index: 1; max-width:100%"></div>
			</div>`
		);
		this.map_area.prependTo(this.$result);
	}

	bind_leaflet_map() {
		var circleToGeoJSON = L.Circle.prototype.toGeoJSON;
		L.Circle.include({
			toGeoJSON: function() {
				var feature = circleToGeoJSON.call(this);
				feature.properties = {
					point_type: 'circle',
					radius: this.getRadius()
				};
				return feature;
			}
		});

		L.CircleMarker.include({
			toGeoJSON: function() {
				var feature = circleToGeoJSON.call(this);
				feature.properties = {
					point_type: 'circlemarker',
					radius: this.getRadius()
				};
				return feature;
			}
		});

		L.Icon.Default.imagePath = '/assets/frappe/images/leaflet/';
		this.map = L.map(this.map_id).fitWorld();

		L.tileLayer('http://{s}.tile.osm.org/{z}/{x}/{y}.png', {
			attribution: '&copy; <a href="http://osm.org/copyright">OpenStreetMap</a> contributors'
		}).addTo(this.map);
	}

	bind_leaflet_draw_control() {
		this.editableLayers = new L.FeatureGroup();

		var options = {
			position: 'topleft',
			draw: {
				polyline: {
					shapeOptions: {
						color: frappe.ui.color.get('blue'),
						weight: 5
					}
				},
				polygon: false,
				marker: false,
				circle: false,
				circlemarker: false,
				rectangle: false
			},
			edit: {
				featureGroup: this.editableLayers,
				remove: false
			}
		};

		// create control and add to map
		var drawControl = new L.Control.Draw(options);

		this.map.addControl(drawControl);

		this.map.on('draw:created', (e) => {
			var type = e.layerType,
				layer = e.layer;
			if (type === 'marker') {
				layer.bindPopup('Marker');
			}
			this.editableLayers.addLayer(layer);
		});

		this.map.on('draw:deleted draw:edited', (e) => {
			var layer = e.layer;
			this.editableLayers.removeLayer(layer);
		});
	}

	render_map() {
		const me = this;
		me.editableLayers = new L.FeatureGroup();
		me.data.forEach(value => {
			me.gelocation_fields.forEach(field => {
				const geometry_value = value[field]
				const data_layers = new L.LayerGroup()
					.addLayer(L.geoJson(JSON.parse(geometry_value),{
						pointToLayer: function(geoJsonPoint, latlng) {
							if (geoJsonPoint.properties.point_type == "circle"){
								return L.circle(latlng, {radius: geoJsonPoint.properties.radius})
									.bindPopup(me.get_popup(value))
									.bindTooltip(me.get_tooltip(value));
							} else if (geoJsonPoint.properties.point_type == "circlemarker") {
								return L.circleMarker(latlng, {radius: geoJsonPoint.properties.radius})
									.bindPopup(me.get_popup(value))
									.bindTooltip(me.get_tooltip(value));
							}
							else {
								return L.marker(latlng)
									.bindPopup(me.get_popup(value))
									.bindTooltip(me.get_tooltip(value));
							}
						}
					}));
				me.add_non_group_layers(data_layers, me.editableLayers);
			})
		})
		try {
			me.map.flyToBounds(me.editableLayers.getBounds(), {
				animate: false,
				padding: [50,50]
			});
		}
		catch(err) {
			// suppress error if layer has a point.
		}
		me.editableLayers.addTo(me.map);

		me.map._onResize();
	}

	add_non_group_layers(source_layer, target_group) {
		// https://gis.stackexchange.com/a/203773
		// Would benefit from https://github.com/Leaflet/Leaflet/issues/4461
		if (source_layer instanceof L.LayerGroup) {
			source_layer.eachLayer((layer)=>{
				this.add_non_group_layers(layer, target_group);
			});
		} else {
			target_group.addLayer(source_layer);
		}
	}

	get_popup(value) {
		const text = Object.keys(this.list_fields).reduce((prev, f) => {
			return `${prev}<p><b>${__(this.list_fields[f])}</b>: ${__(value[f])}</p>`
		}, `<b>${frappe.utils.get_form_link(
			this.doctype,
			value.name,
			true
		)}</b>`)

		return text
	}

	get_tooltip(value) {
		return `<b>${value.name}</b>`
	}
};

