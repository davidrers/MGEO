//Crear una función para crear un tooltip a la capa GeoJSON Población Departamental

function tooltipDepartamentosPoblacion(feature, layer){
	if(feature.properties && feature.properties.cod_dep && feature.properties.dpto && feature.properties.pob2015){

		var tooltipContent  = "<b>Código:</b> " 		+ feature.properties.cod_dep 			 +		 
							  "<br><b>Nombre:</b> " 	+ feature.properties.dpto	 			 + 
							  "<br><b>Área:</b> " 	    + feature.properties.pob2015;
		
		layer.bindTooltip(tooltipContent, {
				permanent	: false,
				direction   : "top",
				offset		: [0, 0],
				className	: "tooltip-dpto"
		});

		//Estilo resaltado del polígono del GeoJSON Población Departamental
		var resaltadoStyle = {
				color 	: "#00ff00",
				weight  : 8
		};

		//Estilo originar del polígono del GeoJSON Población Departamental
		var originalStyle = {
				color 		: "white",
				weight		: 2,
				opacity 	: 1,
				dashArray   : "5, 5"
		};

		//Evento mouseover: para resaltar o cambiar el estilo original del polígono
		layer.on("mouseover", function(e){
			layer.setStyle(resaltadoStyle)
		});

		//Evento mouseout: para volver o cambiar el estilo original del polígono
		layer.on("mouseout", function(e){
			layer.setStyle(originalStyle)
		});
	}
};