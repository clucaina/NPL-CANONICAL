# NeuroCity · verificación física de edificios (Catastro BU + LiDAR)

Estado: **integración opcional, sin despliegue**. Se conservan las huellas originales OSM si la coincidencia geométrica no es inequívoca.

## Fuentes públicas
- INSPIRE BU de la Dirección General del Catastro: https://www.catastro.hacienda.gob.es/webinspire/
- WFS BuildingPart y límites de 4 km² / 5.000 elementos: https://www.catastro.hacienda.gob.es/webinspire/documentos/inspire-bu-wfs.pdf
- Licencia que condiciona redistribución a transformación del producto: https://www.catastro.hacienda.gob.es/webinspire/documentos/Licencia.pdf
- PNOA LiDAR: https://pnoa.ign.es/web/portal/pnoa-lidar/productos-a-descarga

Las plantas catastrales no son alturas físicas: **plantas × 3 m** se marca como estimación, nunca como medida LiDAR.

## Procedimiento

1. Obtener una respuesta GML oficial BU.BUILDINGPART de un BBOX de Alicante, en EPSG:25830.
2. Guardar el GML original de forma LOCAL en demos/npl-world/open_city_pipeline/input/catastro_building_parts.gml. No subirlo al repositorio ni distribuirlo.
3. Instalar bibliotecas públicas: python3 -m pip install pyproj==3.7.2 shapely==2.1.2.
4. Ejecutar tools/neurocity/catastro_parts.py pasando --gml, --osm, --manifest, --official-url y --output. La URL declarada debe coincidir con la descarga real.
5. Guardar JSON normalizado con nombre catastro_building_parts.json junto al GML y al source_manifest.json locales.
6. Ejecutar Blender mediante build_blender.py. El motor verifica SHA-256 del GML, no acepta procedencia simulada y solo dibuja volúmenes catastrales si la geometría corresponde con seguridad a la huella OSM; el resto permanece original.
7. Consultar QA_source_report.json para edificios sustituidos, partes construidas, hash de GML y clasificación de altura ESTIMADA.
8. Ejecutar pruebas: python3 -m unittest discover -s tools/neurocity -p test_catastro_parts.py -v. CI comprueba también Blender real con fuentes sintéticas.

## Por qué no se certifica fotorrealismo

Aún falta LiDAR que mida suelo y cubierta, clasificación de puntos, registro temporal, transformación de datums, huecos y análisis de incertidumbre. Tampoco se ha recuperado la geometría fotorrealista de las fachadas. No se utilizan pacientes, propietarios, identificadores de parcelas ni avatares privados.