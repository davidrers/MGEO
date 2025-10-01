//Crear una función para crear un popup a la capa GeoJSON Restos Arqueologicos
function popupRestosArqueologicos(feature, layer){
	if(feature.properties && feature.properties.NOMBRE){
		layer.bindPopup("<b>Nombre:</b> " + feature.properties.NOMBRE);
	}
};

//Crear una función para crear un popup a la capa GeoJSON Pasivos Ambientales Mineros
function popupPasivosAmbientalesMineros(feature, layer){
	if(feature.properties && feature.properties.PASIVO && feature.properties.CLASE){
		layer.bindPopup("<b>Pasivo:</b> " 		+ feature.properties.PASIVO + 
						"<br><b>Clase:</b> " 	+ feature.properties.CLASE);
	}
};

//Crear una función para crear un popup a la capa GeoJSON Red Hídrica
function popupRedHidrica(feature, layer){
	if(feature.properties && feature.properties.Nombre && feature.properties.Rasgo_Prin && feature.properties.Rasgo_Secu){
		layer.bindPopup("<b>Nombre:</b> " 				+ feature.properties.Nombre + 
						"<br><b>Rasgo Principal:</b> " 	+ feature.properties.Rasgo_Prin + 
						"<br><b>Rasgo Principal:</b> " 	+ feature.properties.Rasgo_Secu);
	}
};

//Crear una función para crear un popup con imagen a la capa GeoJSON Límite Departamental
function popupLimiteDepartamental(feature, layer){
	if(feature.properties && feature.properties.cod_dep && feature.properties.dpto && feature.properties.area_km2){
		//<img src="images/limite_departamental/AMAZONAS.jpg" class = "popup-img-dpto">

		var ruta_img_dpto = '<img src="images/limite_departamental/' + feature.properties.dpto + '.jpg" class = "popup-img-dpto">';
		//console.log(ruta_img_dpto);

		var popupContent  = "<b>Código:</b> " 		+ feature.properties.cod_dep 			 +		 
							"<br><b>Nombre:</b> " 	+ feature.properties.dpto	 			 + 
							"<br><b>Área:</b> " 	+ feature.properties.area_km2.toFixed(2) + " km²" +
							"<br><br>" 				+ ruta_img_dpto;
		
		layer.bindPopup(popupContent);
	}
};