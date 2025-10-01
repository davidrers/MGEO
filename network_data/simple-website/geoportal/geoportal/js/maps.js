//Crear un objeto mapa
var map = L.map("map").setView([-9.195,-74.947],6);

//-----------------------------------------------------------------------------------------------------

//Enlazar el Mapa Base del OpenStreetMap
var osm = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png");

//Enlazar el Mapa Base del Blanco y Negro de Carto
var blackAndWhite = L.tileLayer("http://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png").addTo(map);

//Enlazar el mapa base de Calles de Google Earth
var googleStreets = L.tileLayer('https://mt1.google.com/vt/lyrs=r&x={x}&y={y}&z={z}');

//Enlazar el mapa base de Satélite de Google Earth
var googleSat = L.tileLayer('http://www.google.cn/maps/vt?lyrs=s@189&gl=cn&x={x}&y={y}&z={z}');

//Enlazar el mapa base de Relieve de ESRI
var terrain = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}');

//Enlazar el mapa base de National Geographic
var natGeo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}');

//-----------------------------------------------------------------------------------------------------
//Añadir Archivos GeoJSON de Restos Arqueológicos
var restos_arqueologicos = L.geoJSON(restos_arqueologicos, {
															pointToLayer: function(feature, latlng){
																					return L.marker(latlng, {
																							icon: restos_arqueologicos_icon
																					})
																},
															onEachFeature: popupRestosArqueologicos 	
});

//Añadir Archivos GeoJSON de Pasivos Ambientales Mineros con cluster
var cluster_pam = L.markerClusterGroup();

var pam 				 = L.geoJSON(pasivos_ambientales_mineros, {
													onEachFeature: function(feature, layer){
															cargarIconPam(feature, layer);
															popupPasivosAmbientalesMineros(feature, layer)
													}
});

cluster_pam.addLayer(pam);
//map.addLayer(cluster_pam);
//cluster_pam.addTo(map);

//Añadir Archivos GeoJSON de Red Hídrica
var red_hidrica = L.geoJSON(red_hidrica, {
											style	      : rasgo_principal_rh_style,
											onEachFeature : popupRedHidrica
});

//Añadir Archivos GeoJSON de Departamentos
var limite_departamental = L.geoJSON(departamentos, {
												style 		  : limite_departamental_styles,
												onEachFeature : popupLimiteDepartamental
});

//Añadir Archivos GeoJSON de Departamentos con su Campo Población
var departamentos_poblacion = L.geoJSON(departamentos, {
											style 			: cargarStylePob2015,
											onEachFeature   : tooltipDepartamentosPoblacion
});

//Crear un Mapa de Calor
//https://github.com/mourner/simpleheat
var heatData = pasivos_ambientales_mineros.features.map(function(feature){
					return [feature.geometry.coordinates[1], feature.geometry.coordinates[0]];
});

var heatLayer = L.heatLayer(heatData, {radius: 100});

//Función para activar el heatLayer
document.getElementById("activarHeatmap").onclick = function(){
	if(!map.hasLayer(heatLayer)){
		map.addLayer(heatLayer);
	}
};

//Función para desactivar el heatLayer
document.getElementById("desactivarHeatmap").onclick = function(){
	if(map.hasLayer(heatLayer)){
		map.removeLayer(heatLayer);
	}
};


//console.log(pasivos_ambientales_mineros);
//-----------------------------------------------------------------------------------------------------
//Conectar Srvicio WFS
//https://github.com/calvinmetcalf/leaflet-ajax
var tunelesANA_wfs     = "https://geosnirh.ana.gob.pe/server/services/P%C3%BAblico/Tuneles/MapServer/WFSServer?service=WFS&version=2.0.0&request=GetFeature&typeName=Tuneles:BDInventario.dbo.Tunel_AAA_Todas&OUTPUTFORMAT=GEOJSON";
var tunelesANA_geojson = new L.GeoJSON.AJAX(tunelesANA_wfs);

//-----------------------------------------------------------------------------------------------------
//Cargar Información ráster
var relieve_punto1 		= L.latLng(-0.050377541,-81.666221516);
var relieve_punto2 		= L.latLng(-18.450855722,-68.332541676);

var georreferenciacion 	= L.latLngBounds(relieve_punto1, relieve_punto2);
var ruta_img_relieve	= "layers/raster/relieve4326.png";

var ruta_img_relieve	= L.imageOverlay(ruta_img_relieve, georreferenciacion);

//-----------------------------------------------------------------------------------------------------

//HERRAMIENTAS, TOOLS, CONTROLES, FUNCIONES

//Agregar el Control de Localización (GPS)
//https://github.com/domoritz/leaflet-locatecontrol
L.control.locate({
					position			: "topleft",
					strings				: {
											title: "Mostrar mi ubicación"
					},
					locateOptions		: {
											maxZoom: 6
					},
    				keepCurrentZoomLevel: true,
    				flyTo				: true,
    				setView				: true
}).addTo(map);

//Agregar un MiniMap o Mapa de Ubicación
//https://github.com/Norkart/Leaflet-MiniMap
new L.Control.MiniMap(googleSat, {
									position		: "bottomleft",
									toggleDisplay	: true,
									minimized		: true,
									strings			: {
														showText		: 'Mostrar Mapa de Ubicación',
														hideText		: 'Ocultar Mapa de Ubicación'
													 }
}).addTo(map);

//Agregar Control de Escala
//https://leafletjs.com/reference.html#control-scale
L.control.scale({
					imperial	: false,
					position	: "bottomleft"
}).addTo(map);

//Agregar una barra de coordenadas
//https://github.com/MrMufflon/Leaflet.Coordinates
L.control.coordinates({
						position			: "topright",
						decimals			: 6,
						decimalSeperator	: ",",
						labelTemplateLng	: "Longitud:  {x}",
						labelTemplateLat	: "Latitud:  {y}",
						useLatLngOrder		: false,
						enableUserInput		: true,
						useDMS				: true
}).addTo(map);


//Buscado de direcciones
//https://github.com/perliedman/leaflet-control-geocoder
L.Control.geocoder({
						position		: "topleft",
						placeholder		: "Buscar...",
						errorMessage	: "No se encontraron resultados de su dirección."
						//geocoder		: L.Control.Geocoder.esri()

}).addTo(map);

//L.Control.Geocoder.mapbox('YOUR_MAPBOX_ACCESS_TOKEN')
//L.Control.Geocoder.esri()
//L.Control.Geocoder.bing('YOUR_BING_MAPS_KEY')para google maps pero con
//L.Control.Geocoder.extend

//Crear un control de busqueda de atributos de una capa GeoJSON (Search-Control)
//https://github.com/stefanocudini/leaflet-search
var searchControl = new L.Control.Search({
							layer 		 	: limite_departamental,
							propertyName 	: "dpto",
							moveToLocation	: function(latlng, title, map){
												var zoom = map.getBoundsZoom(latlng.layer.getBounds());
												map.setView(latlng, zoom);

							},
							marker 			: false
});

//Evento que se ejecute cuando se encuentre una ubicación de busqueda ('search:locationfound')
searchControl.on('search:locationfound', function(e){
	e.layer.setStyle({
		color 	: "#0f0",
		weight	: 8
	});
	if(e.layer._popup){
		e.layer.openPopup();
	}
}).on('search:collapsed', function(e){
	limite_departamental.eachLayer(function(layer){
		limite_departamental.resetStyle(layer)
	});
});

map.addControl(searchControl);

//Agregar Sidebar
var sidebar = L.control.sidebar({
									container	: "sidebar",
									position 	: "left",
									autopan		: true
}).addTo(map);

sidebar.open("home");




//--------------------CONFIGURACIÓN DE CONTROLADOR DE CAPAS-------------------------------
//Diccionario de Mapas Base

var baseMaps	= {
					"Desactivar Mapas Base" :   L.layerGroup([]),
					"OpenStreetMap"			: 	osm,
					"Blanco y Negro"		: 	blackAndWhite,
					"Calles de Google"		: 	googleStreets,
					"Satélite de Google"	: 	googleSat,
					"Relieve	"			: 	terrain,
					"National Geographic"	: 	natGeo
};

//Diccionar de Capas
var layers		= {
					"Restos Arqueológicos"			:   restos_arqueologicos,
					"Pasivos Ambientales Mineros"	:   cluster_pam,
					"Red Hídrica"					:   red_hidrica,
					"Departamentos"					:   limite_departamental,
					"Población 2015"				:   departamentos_poblacion,
					"Túneles WFS"					:   tunelesANA_geojson,
					"Relieve Ráster"				:   ruta_img_relieve
};

//Añadir controlador de capas
L.control.layers(baseMaps, layers).addTo(map);

//--------------------------------------------------------------------------------------------
//Añadir Leyenda
//https://github.com/ptma/Leaflet.Legend

var leyenda = L.control.Legend({
					title		: "LEYENDA",
					position 	: "bottomright",
					collapsed   : false,
					opacity 	: 1,
					legends		: [
									{
										label 	: "Restos Arqueológicos",
										type    : "image",
										url     : "plugins/images/restos_arqueologicos.png",
										//layers  : restos_arqueologicos
									},

									{
										label 	: "Río Principal",
										type 	: "polyline",
										color	: "blue",
										weight	: 4,
										opacity : 1,
										layers  : red_hidrica
									},

									{
										label 		: "Río Secundario",
										type 		: "polyline",
										color 		: "#5dc1b9", // Color de la línea negro
						                weight 		: 2.5, // Grosor de la línea
						                opacity 	: 1, // Opacidad de la línea
						                layers  	: red_hidrica
									},

									{
										label 		: "Límite Departamental",
										type 		: "rectangle",
										color		: "#FFFF00",
										weight		: 2,
										dashArray	: [5, 5, 1],
										layers  	: limite_departamental
										
									},

									{
										label 		: "0 a 500 000 hab.",
										type 		: "rectangle",
										fillColor   : "#ffffd4",
										fillOpacity : 1,
										color		: "black",
										weight		: 0.5,
										opacity 	: 1,
										layers  	: departamentos_poblacion
										
									},

									{
										label 		: "500 00 a 800 000 hab.",
										type 		: "rectangle",
										fillColor   : "#fed98e",
										fillOpacity : 1,
										color		: "black",
										weight		: 0.5,
										opacity 	: 1,
										layers  	: departamentos_poblacion
										
									},

									{
										label 		: "800 000 a 1 200 000 hab.",
										type 		: "rectangle",
										fillColor   : "#fe9929",
										fillOpacity : 1,
										color		: "black",
										weight		: 0.5,
										opacity 	: 1,
										layers  	: departamentos_poblacion
										
									},

									{
										label 		: "1 200 000 a 1 500 000 hab.",
										type 		: "rectangle",
										fillColor   : "#d95f0e",
										fillOpacity : 1,
										color		: "black",
										weight		: 0.5,
										opacity 	: 1,
										layers  	: departamentos_poblacion
										
									},

									{
										label 		: "1 500 000 a más hab.",
										type 		: "rectangle",
										fillColor   : "#993404",
										fillOpacity : 1,
										color		: "black",
										weight		: 0.5,
										opacity 	: 1,
										layers  	: departamentos_poblacion
										
									}
						]	
}).addTo(map);


