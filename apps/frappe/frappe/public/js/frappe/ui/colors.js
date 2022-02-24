// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
// MIT License. See license.txt

frappe.provide("frappe.ui");

// frappe.ui.color_map = {
// 	red: ["#ffc4c4", "#ff8989", "#ff4d4d", "#a83333"],
// 	brown: ["#ffe8cd", "#ffd19c", "#ffb868", "#a87945"],
// 	orange: ["#ffd2c2", "#ffa685", "#ff7846", "#a85b5b"],
// 	peach: ["#ffd7d7", "#ffb1b1", "#ff8989", "#a84f2e"],
// 	yellow: ["#fffacd", "#fff168", "#fff69c", "#a89f45"],
// 	yellowgreen: ["#ebf8cc", "#d9f399", "#c5ec63", "#7b933d"],
// 	green: ["#cef6d1", "#9deca2", "#6be273", "#428b46"],
// 	cyan: ["#d2f8ed", "#a4f3dd", "#77ecca", "#49937e"],
// 	skyblue: ["#d2f1ff", "#a6e4ff", "#78d6ff", "#4f8ea8"],
// 	blue: ["#d7e4ff", "#9cbcff", "#6195ff", "#003aaf"],
// 	purple: ["#dac7ff", "#b592ff", "#8e58ff", "#5e3aa8"],
// 	pink: ["#f8d4f8", "#f3aaf0", "#ec7dea", "#934f92"],
// 	white: ["#d1d8dd", "#fafbfc", "#ffffff", ""],
// 	black: ["#778595", "#6c7680", "#36414c", "#212a33"]
// };

frappe.ui.color = {
	get: function(color_name, shade) {
		if(color_name && shade) return this.get_color_shade(color_name, shade);
		if(color_name) return this.get_color_shade(color_name, 'default');
		return frappe.ui.color_map;
	},
	get_color: function(color_name) {
		const color_names = Object.keys(frappe.ui.color_map);
		if(color_names.includes(color_name)) {
			return frappe.ui.color_map[color_name];
		} else {
			// eslint-disable-next-line
			console.warn(`'color_name' can be one of ${color_names} and not ${color_name}`);
		}
	},
	get_color_map() {
		const colors = ['red', 'green', 'blue', 'dark-green', 'yellow', 'gray', 'purple', 'pink', 'orange'];
		const shades = ['100', '300', '500', '700'];
		const style = getComputedStyle(document.body);
		let color_map = {};
		colors.forEach(color => {
			color_map[color] = shades.map(shade =>
				style.getPropertyValue(`--${color}-${shade}`).trim()
			);
		});
		return color_map;
	},
	get_color_shade: function(color_name, shade) {
		const shades = {
			'default': 2,
			'light': 1,
			'extra-light': 0,
			'dark': 3
		};

		if(Object.keys(shades).includes(shade)) {
			const color = this.get_color(color_name);
			return color ? color[shades[shade]] : color_name;
		} else {
			// eslint-disable-next-line
			console.warn(`'shade' can be one of ${Object.keys(shades)} and not ${shade}`);
		}
	},
	all: function() {
		return Object.values(frappe.ui.color_map)
			.reduce((acc, curr) => acc.concat(curr) , []);
	},
	names: function() {
		return Object.keys(frappe.ui.color_map);
	},
	is_standard: function(color_name) {
		if(!color_name) return false;
		if(color_name.startsWith('#')) {
			return this.all().includes(color_name);
		}
		return this.names().includes(color_name);
	},
	get_color_name: function(hex) {
		for (const key in frappe.ui.color_map) {
			const colors = frappe.ui.color_map[key];
			if (colors.includes(hex)) return key;
		}
	},
	get_contrast_color: function(hex) {
		if(!this.validate_hex(hex)) {
			return;
		}

		if (this.is_standard(hex)) {
			const color_name = this.get_color_name(hex);
			const colors = this.get_color(color_name);
			const shade_value = colors.indexOf(hex);
			if(shade_value <= 1) {
				return this.get(color_name, 'dark');
			}
		}

		const brightness = this.brightness(hex);
		if(brightness < 150) {
			return this.lighten(hex, 1);
		}
		return this.lighten(hex, -1);
	},

	validate_hex: function(hex) {
		// https://stackoverflow.com/a/8027444/5353542
		return /(^#[0-9A-F]{6}$)|(^#[0-9A-F]{3}$)/i.test(hex);
	},

	lighten(color, percent) {
		// https://stackoverflow.com/a/13542669/5353542
		return pSBC(percent, color);
	},

	hex_to_rgb(hex) {
		if(hex.startsWith('#')) {
			hex = hex.substring(1);
		}
		const r = parseInt(hex.substring(0, 2), 16);
		const g = parseInt(hex.substring(2, 4), 16);
		const b = parseInt(hex.substring(4, 6), 16);
		return {r, g, b};
	},

	brightness(hex) {
		const rgb = this.hex_to_rgb(hex);
		// https://www.w3.org/TR/AERT#color-contrast
		// 255 - brightest (#fff)
		// 0 - darkest (#000)
		return (rgb.r * 299 + rgb.g * 587 + rgb.b * 114) / 1000;
	}
};

const pSBC=(p,c0,c1,l)=>{
	let r,g,b,P,f,t,h,i=parseInt,m=Math.round,a=typeof(c1)=="string";
	if(typeof(p)!="number"||p<-1||p>1||typeof(c0)!="string"||(c0[0]!='r'&&c0[0]!='#')||(c1&&!a))return null;
	if(!this.pSBCr)this.pSBCr=(d)=>{
		let n=d.length,x={};
		if(n>9){
			[r,g,b,a]=d=d.split(","),n=d.length;
			if(n<3||n>4)return null;
			x.r=i(r[3]=="a"?r.slice(5):r.slice(4)),x.g=i(g),x.b=i(b),x.a=a?parseFloat(a):-1
		}else{
			if(n==8||n==6||n<4)return null;
			if(n<6)d="#"+d[1]+d[1]+d[2]+d[2]+d[3]+d[3]+(n>4?d[4]+d[4]:"");
			d=i(d.slice(1),16);
			if(n==9||n==5)x.r=d>>24&255,x.g=d>>16&255,x.b=d>>8&255,x.a=m((d&255)/0.255)/1000;
			else x.r=d>>16,x.g=d>>8&255,x.b=d&255,x.a=-1
		}return x};
	h=c0.length>9,h=a?c1.length>9?true:c1=="c"?!h:false:h,f=this.pSBCr(c0),P=p<0,t=c1&&c1!="c"?this.pSBCr(c1):P?{r:0,g:0,b:0,a:-1}:{r:255,g:255,b:255,a:-1},p=P?p*-1:p,P=1-p;
	if(!f||!t)return null;
	if(l)r=m(P*f.r+p*t.r),g=m(P*f.g+p*t.g),b=m(P*f.b+p*t.b);
	else r=m((P*f.r**2+p*t.r**2)**0.5),g=m((P*f.g**2+p*t.g**2)**0.5),b=m((P*f.b**2+p*t.b**2)**0.5);
	a=f.a,t=t.a,f=a>=0||t>=0,a=f?a<0?t:t<0?a:a*P+t*p:0;
	if(h)return"rgb"+(f?"a(":"(")+r+","+g+","+b+(f?","+m(a*1000)/1000:"")+")";
	else return"#"+(4294967296+r*16777216+g*65536+b*256+(f?m(a*255):0)).toString(16).slice(1,f?undefined:-2)
}

frappe.ui.color_map = frappe.ui.color.get_color_map();