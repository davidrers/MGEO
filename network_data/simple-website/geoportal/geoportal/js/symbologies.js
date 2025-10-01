//Crear simbología simple para líneas
var red_hidrica_styles = {
							color		: "#00cdff",
							weight		: 4,
							opacity 	: 1,
							dashArray	: "5, 5, 1"
};

//Crear una Funciónpara cambiar los estilos de líneas con varias categorías.
function rasgo_principal_rh_style(feature){
	switch(feature.properties.Rasgo_Prin){

		case "Río Principal":
			return{
				color	: "blue",
				weight	: 4,
				opacity : 0.7
				  };

		case "Río Secundario":
            return {
                color: "#5dc1b9", // Color de la línea negro
                weight: 2.5, // Grosor de la línea
                opacity: 0.7, // Opacidad de la línea
            };

        case 'Río Seco':
            return {
                color: "brown", // Color de la línea negro
                weight: 1.5, // Grosor de la línea
                opacity: 0.7, // Opacidad de la línea
            };

        case 'Quebrada Húmeda':
            return {
                color: "red", // Color de la línea negro
                weight: 1.5, // Grosor de la línea
                opacity: 0.7, // Opacidad de la línea
                dashArray: '5, 10' // Patrón de línea discontinua (5px de línea, 5px de espacio)
            };

        case 'Quebrada Seca':
            return {
                color: "orange", // Color de la línea negro
                weight: 1.5, // Grosor de la línea
                opacity: 0.7, // Opacidad de la línea
                dashArray: '5, 10' // Patrón de línea discontinua (5px de línea, 5px de espacio)
            };

	}
};

//Crear simbología simple para polígonos
var limite_departamental_styles = {
									color		: "yellow",
									weight		: 2,
									dashArray	: "5, 5",
									fillOpacity : 0
									};

//Crear una función para obtener el color según rango de población
function obtenerPob2015(pob2015){
									return pob2015 <= 500000	?	"#ffffd4":
									       pob2015 <= 800000	?	"#fed98e":
									       pob2015 <= 1200000	?	"#fe9929":
									       pob2015 <= 1500000	?	"#d95f0e":
									       							"#993404";
};

//Crear la función que va añadir los colores de los rangos a la capa de población
function cargarStylePob2015(feature){
	return {
				fillColor	: obtenerPob2015(feature.properties.pob2015),
				fillOpacity : 0.7,
				color 		: "white",
				weight		: 2,
				opacity 	: 1,
				dashArray   : "5, 5"
	};
};



















