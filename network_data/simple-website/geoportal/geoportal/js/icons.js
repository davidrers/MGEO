//Crear ícono personalizado para restos arqueológicos
var restos_arqueologicos_icon =		L.icon({
												iconUrl		: "plugins/images/restos_arqueologicos.png",
												iconSize	: [50, 50],
												iconAnchor	: [25, 25],
												popupAnchor	: [0, -25]
									});

//Crear ícono personalizado para Pasivos Ambientales Mineros Abandonados
var pam_abandonado_icon =		L.icon({
												iconUrl		: "plugins/images/pam_abandonado.png",
												iconSize	: [20, 20]
									});

//Crear ícono personalizado para Pasivos Ambientales Mineros Inactivos
var pam_inactivo_icon =		L.icon({
												iconUrl		: "plugins/images/pam_inactivo.png",
												iconSize	: [20, 20]
									});

//Crear una función para obtener el Ícono correcto de los pasivos ambientales mineros
function obtenerIconPam(feature){

	if (feature.properties.CLASE === "ABANDONADO"){
		return pam_abandonado_icon;

	} else if (feature.properties.CLASE === "INACTIVO"){
		return pam_inactivo_icon;
	}

};


//Crear una Función para añadir el ícono correcto de los pasivos ambientales mineros
function cargarIconPam(feature, layer){
	layer.setIcon(obtenerIconPam(feature));
};
