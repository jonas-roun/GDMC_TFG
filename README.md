# GDMC\_TFG v1.0

## Descripción

Proyecto de TFG que genera una ciudad de manera procedimental utilizando algoritmos genéticos para la disposición de parcelas en una ciudad. Permite generar ciudades dado un número de parcelas y un terreno según criterios de desnivel, agua y superposición de parcelas.

## Características

* Generación automática de parcelas.
* Evaluación de ciudades mediante función de fitness considerando penalizaciones por agua y desnivel.
* Algoritmo genético con selección, cruce y mutación.
* Control de solapamiento de parcelas mediante matriz de ocupación.
* Mutaciones de movimiento y redimensionamiento de parcelas con validación de ciudad.
* Allanamiento de las parcelas creadas para su posterior construcción

## Requisitos

* Python 3.10 o superior.
* gdpc

## Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/jonas-roun/GDMC_TFG/tree/master
```

2. Instalar gdpc para conectarse con Minecraft:

```bash
pip install -r gdpc
```

3. Instalar el [mod de Minecraft que hace de interfaz con el cliente Python](https://github.com/Niels-NTG/gdmc_http_interface)

## Uso

1. Usar el comando /setbuildarea en Minecraft para asignar una zona de construcción
2. Usar la interfaz gráfica para inspeccionar el terreno elegido (si cambiamos el área de construcción con el programa en marcha podremos refrescar los mapas de la interfaz)
3. Indicar el número de parcelas a construir y darle al botón de construir

## Futuras adiciones
* Construcción de casas básicas en las parcelas generadas
* Caminos entre las parcelas
* Refinar el algoritmo para colocar parcelas
* Cambios estéticos
