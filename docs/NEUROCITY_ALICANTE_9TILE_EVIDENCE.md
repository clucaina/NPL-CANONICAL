# NeuroCity · fabricación geográfica escalable | Alicante 3×3

**Estado:** rama experimental PR #34. Los cambios no se han fusionado ni desplegado.

## De un recorte a nueve consultas auditables

El anterior motor incorporaba secciones del Catastro de una única consulta WFS; se comprobó con datos oficiales el reemplazo estricto de **21 de 614 edificios OSM** por 109 partes 3D. El nuevo módulo genera una malla 3×3 en EPSG:25830 a partir de las cuatro esquinas del bbox original, con 35 m de solapamiento: nueve solicitudes pequeñas en lugar de descargar sin control toda Alicante.

Una consulta de 3×3 requiere **nueve** instantáneas oficiales distintas y sus SHA-256. Las geometrías repetidas entre consultas se deduplican por WKB canónico; si la misma planta tiene dos alturas incompatibles, ambas se rechazan. Las partes se asocian GLOBALMENTE al OSM conservando los umbrales de superposición; no se rellenan edificios ausentes con inventos.

## Evidencia inicial, 20/10/2026

GitHub Actions: https://github.com/clucaina/NPL-CANONICAL/actions/runs/39413848074

- Código y exportación Blender de **nueve celdas sintéticas**: SUPERADO.
- WFS real: **6/9** consultas obtenidas; tres conexiones remotas desconectadas.
- GML auténtico: 3.978 partes candidatas; 2.892 partes únicas tras 1.086 duplicados exactos; 0 conflictos de altura duplicada.
- Geometría verificable: **38 edificios** OSM sustituidos por **155 secciones catastrales**; 302 relaciones ambiguas rechazadas; 614 edificios OSM totales preservados como fuente.
- GLB real generado temporalmente por Blender: 1.189.896 bytes, SHA-256 `fc67aa86fa237b865bfa40cf4e408db1969e32a3e1ee81aed67e6e4c52c83e25`.
- Esta ejecución **no** equivale a 9/9 ni a una versión fotogramétrica; la ciudad pública de producción no ha cambiado.

Los tres sectores faltantes son `r1_c2`, `r2_c0` y `r2_c1`, error `RemoteDisconnected`. Se ha añadido una segunda pasada SERIADA con pausa de seis segundos, limitada a los sectores fallidos y sin bucles indefinidos. Las ejecuciones posteriores deben auditarse antes de actualizar esta evidencia.

## Contrato de software

- `tools/neurocity/catastro_grid.py`: genera, valida y normaliza las nueve celdas, preservando hashes y prohibiendo afirmaciones de cobertura completa ante sectores ausentes.
- `tools/neurocity/catastro_grid_live.py`: obtiene OSM una sola vez, consulta WFS con un máximo inicial de dos conexiones, intenta recuperar errores transitorios y destruye GML/GLB tras medir sus propiedades.
- `tools/neurocity/catastro_grid_smoke.py`: construye datos de prueba anónimos procedentes de geometrías sintéticas consistentes con el CRS.
- `demos/npl-world/open_city_pipeline/build_blender.py`: acepta contratos previos v1 o nueva malla v2, verifica SHA-256 de cada GML, mantiene el fallback OSM y triangula cubiertas.
- `.github/workflows/neurocity-grid-3d-qa.yml`: pruebas sin red, exportación 3D sintética y auditoría real; el único artefacto contiene métricas, no la geografía fuente.

### Ejecutar una reconstrucción LOCAL tras descargar las fuentes

1. `python3 -m pip install pyproj==3.7.2 shapely==2.1.2`
2. Preparar `demos/npl-world/open_city_pipeline/input/alicante.osm` y `source_manifest.json` originales del proyecto.
3. Guardar **únicamente en local** las respuestas WFS oficiales en `input/catastro_grid_tiles/r0_c0.gml` hasta `r2_c2.gml`; las URLs generadas con `source_plan(source_manifest['bbox'])` deben coincidir con las peticiones reales.
4. Ejecutar `python3 tools/neurocity/catastro_grid.py --osm demos/npl-world/open_city_pipeline/input/alicante.osm --manifest demos/npl-world/open_city_pipeline/input/source_manifest.json --source-dir demos/npl-world/open_city_pipeline/input/catastro_grid_tiles --output demos/npl-world/open_city_pipeline/input/catastro_building_parts.json --require-complete`.
5. Ejecutar Blender desde la carpeta `demos/npl-world/open_city_pipeline` con `blender -b --factory-startup -t 2 --python-exit-code 1 -P build_blender.py`.
6. Comprobar `output/QA_source_report.json`. No subir fuentes GML ni derivados GLB al repositorio público.

## Límites científicos

- Las plantas BU aportan secciones y número de pisos; **plantas × 3 m es una altura artística ESTIMADA**, no una medición LiDAR. El uso de triangulación no convierte fachadas genéricas en fotogrametría.
- Aún no hay interiores locales, rótulos auténticos de comercios ni fotografías de fachada asociadas a cada edificio; no pueden inventarse por el mero hecho de georreferenciar una huella.
- Un SHA-256 comprueba igualdad de bytes, **no** la autenticidad de una firma pública. El código utiliza HTTPS oficial y validez geográfica, no certificación administrativa de cada superficie.
- No altera el almacén original de NPL, Conflictómetro ni información de pacientes. NPL/Conflictómetro mantienen su contrato de agregados públicos y se tratan como capa independiente de simulación social.
- Las pruebas en CI verifican compilación y exportación; no miden FPS en GPU móvil real ni permiten proclamar 60 FPS.

## Próxima expansión demostrable

La prioridad es completar nueve sectores sin sobrecargar el WFS, preservar las fuentes para ejecución local del usuario y **conectar un modelo derivado validado con una revisión visual de Chromium sin desplegarlo**. Tras esa etapa, geometría de techos y fachadas con alturas relativas obtenidas de LiDAR-PNOA (cota de superficie menos suelo), pruebas multitemporales, clasificación y errores de datum; después tiling/LOD y pruebas de movilidad por distancias reales. Para España se requiere un coordinador de ciudades y límites oficiales verificados, no reutilizar fuera de Alicante esta malla rígida como si fuera universal.

Fuentes oficiales: [Catastro INSPIRE](https://www.catastro.hacienda.gob.es/webinspire/), [PNOA-LiDAR](https://pnoa.ign.es/web/portal/pnoa-lidar/productos-a-descarga).