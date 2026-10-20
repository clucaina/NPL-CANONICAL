# NeuroCity — Conservación del mundo maestro y producción reproducible de España
**Estado:** ingeniería experimental en rama independiente. **NO DESPLEGAR / NO FUSIONAR / NO RECOMPARTIR** los activos originales antes de revisar derechos individualmente.

## Por qué se habían perdido visualmente los avances
Las iteraciones geográficas basadas sólo en `open_city_pipeline` y `visual_viewer` regeneraban un subconjunto de Alicante con OSM y PNOA, pero ignoraban el mundo maestro generado anteriormente por las líneas internas de trabajo. No era inexistencia de modelos; faltaba un contrato de recuperación + coordenadas + versiones de motor. No sustituir una colección de edificios decorativos por un único modelo degradado.

## Fuente REAL recuperada y controles
Un ZIP preexistente del usuario, `NEUROCITY_WORLD_MASTER_CHECKPOINT_INTEGRACION.zip`, contiene un manifiesto de procedencia, 107 registros originales de hash y 83 GLB con geometrías estructuralmente legibles, repartidos en teselas originales, V50, farolas, objetos de pavimento, 6 variantes de Phoenix, escaparates interpretados, Casa Carbonell, puerto y costa.
- 107 de 107 entradas referenciadas pasaron comprobación de SHA256/tamaño en su archivo de origen; el auditor no altera bytes.
- Extractor local genera 75 archivos GLB únicos para cuatro teselas de 500 m, con colocaciones aproximadas de 63 palmeras de las seis variantes originales y 64.8 MB de binarios originales.
- ETRS89 EPSG:25830 (centro E=719700,N=4248300) -> visor Mercator EPSG:3857 (centro 38.34402,-0.48322) por puente afín **aproximado** (residuo observado local ~0.38m). No declarar precisión milimétrica ni datum vertical verificado.
- Renderizador actual Three r169 recibe las teselas fuente nativas: no cargar el antiguo visor r128 ni sustituir el juego. La base OSM/PNOA conserva su prioridad si falla cualquier comprobación.
- La carga es optativa y LOCAL: `http://127.0.0.1:8766/?worldmaster=1` usando el paquete de recuperación; al ejecutar la versión pública del repositorio sin los bytes de Drive, solo se muestra ciudad OSM habitual.
- La reproducción completa de los 75 GLB juntos en Chromium **no se ha certificado**: el entorno local de navegador agotó el tiempo de arranque sin imagen. Pruebas unitarias Three y esbuild sí se ejecutaron en Actions; la captura vieja del mundo maestro no equivale a un pase E2E del visor nuevo.

## Ruta verificable de dos entregas, sin pérdidas
**Capa de código publicable (sólo ingeniería):** `worldmaster_recovery.py`, `export_local_worldmaster.py`, `geo_alignment.mjs`, `city_tiles.mjs`, `world_master_loader.mjs`, tests y workflow sin GLBs. GitHub PR en borrador.

**Capa binaria restringida al propietario:** ZIP con fuente de Drive y 75 GLB, MOSAICO V50, teselas originales, muestras visuales y manifiestos. Verificar derecho individual de fotos, edificios, marcas y texturas antes de publicación. Nunca guardar este ZIP en el repositorio público ni publicarlo como Creative Commons propio.

## Cadena de producción por teselas para ciudades españolas
`tools/neurocity/spain_tile_factory.py` permite declarar cajas espaciales oficiales proyectadas y planificar lotes independientes de 250, 500 o 1.000 m; sus límites de cuota impiden afirmar que toda España se ha generado con una sola ejecución. Para cada tesela los ocho pasos son: auditar OSM/PNOA, suelo/vías, alturas LiDAR, fuentes de fachadas, GLB, navegación, experiencias didácticas NPL/Conflictómetro, revisión visual/licencia.

El planificador valida SHA256 y permisos para fuentes OSM, ortofoto, LiDAR y fotos por separado. Sin fuente verificada marca BLOQUEO, **nunca inventa modelos**. Los futuros consumidores deben usar caché de geometría por SHA, materiales KTX2, HLOD, streaming por distancia, ETag, presupuestos CPU/GPU y workers para evitar que 20.000 teselas arruinen la experiencia de uso. La CDN/despliegue son decisiones futuras y no se han iniciado.

## Tiendas, interiores, marcas, trabajadores y experiencia MMO
- Locales públicos: OSM/registro abierto de rótulos, fotos de exterior con derechos revisados, tiempo/fecha y fuentes. Los negocios cambian y nombres/marcas no prueban diseño de interior o actividad.
- Interiores: opt-in de comercios, modelos CC0 identificados como interiores ficticios o levantamientos interiores autorizados. No inferir la estructura real de tiendas o pisos desde fotos de fachada.
- Personajes: NPC inventados o avatares voluntarios, sin generar semejanzas biométricas de personas reales ni atribuir identidades o profesiones inventadas a trabajadores.
- Multijugador: necesita servidor con autenticación/consentimiento, control de abuso, moderación, privacidad desde el diseño, sincronización de movimiento, persistencia, límites de presencia. **No existe todavía un MMO operativo en esta rama.**
- Progresión no violenta: retos de verificación de indicadores públicos, aprendizaje de psicología, resolución constructiva de conflictos y cooperación sin atacar ni diagnosticar a personas reales.
- No subir expedientes, direcciones domésticas sensibles, rostros ni datos periciales. NPL/Conflictómetro permanecen en contratos públicos de agregados, originales intactos.

## Definición auditable de «terminado»
Una ciudad no puede declararse milimétrica por estar texturizada. Para cada sector: densidad real de LiDAR/ortofoto, errores GPS/ortorrectificación, precisión vertical, completitud de fachadas, fuente/fecha/licencia de locales, contrastes de fotos callejeras, flujos de accesibilidad y métricas FPS p50/p95 de equipos reales. Resultados desconocidos = desconocidos; visualizaciones artísticas = artísticas.

## Pruebas
La ejecución `neurocity-worldmaster-recovery-qa.yml` instala Node y Three.js y comprueba determinismo, matrices de proyección, seguridad de rutas, límites de carga, fallbacks, compatibilidad de render r169 y código del juego. Python comprueba bytes, hashes, archivos sintéticos malformados, cuatro sectores y CRS regionales para la futura fábrica española. Solo archivos sintéticos se usan en GitHub Actions, no se copian originales del usuario.

## Iteración posterior · fidelidad geométrica, presupuesto y visualización (20/10/2026)
**Verificado sobre originales del propietario, no generado a partir de fotografías ajenas:**
- 75 GLB únicos, **899.328 triángulos estimados** según los accesores `POSITION`/`indices`, 1.017 mallas y 47 imágenes integradas; la geometría acumulada incluye variantes y no significa que todo se dibuje simultáneamente.
- Render CPU independiente con VTK + Xvfb de **17 GLB originales combinados** del sector Explanada, incluidos mosaico V50, los seis Phoenix, arquitectura, mobiliario y costa. Artefacto de revisión privada; **no es captura del juego ni aprobado por fotometría**. Muestra errores visibles de plano costero y falta de detalle de edificios; no ocultarlos.
- `asset_instancing.mjs`: reutiliza geometría/materiales originales con `InstancedMesh`, en vez de clonar las decenas de mallas; muestreo móvil determinista y draw calls acotadas.
- `worldmaster_recovery.py` y `export_local_worldmaster.py`: añaden triángulos e imágenes auditados por GLB al manifiesto local. `city_tiles.mjs` limita geometría por perfil (290.000 móvil, 1.500.000 escritorio de presupuesto objetivo para una tesela), conserva terreno+arquitectura+mosaico y descarta opcionales costosos cuando no caben. Los triángulos originales son estimaciones de metadata, no perfil GPU real.
- Cada transferencia GLB local ahora comprueba **tamaño exacto y SHA-256 con WebCrypto antes de que el cargador GLTFLoader interprete los bytes**. Una copia corrupta no se convierte silenciosamente en un modelo aparentemente real.
- `osm_building_mask.mjs` recorta únicamente paredes/tejados OSM bajo teselas maestras listas; mantiene PNOA y las superficies viarias OSM para que nunca desaparezca la ciudad completa al cargarse un sector.
- `geo_alignment.mjs` tiene **cuatro matrices por tesela EPSG:25830 -> EPSG:3857**, calculadas con PROJ en vez de la anterior única matriz afín. Residuo de la aproximación de proyección en la cuadrícula 7×7 **menor de 0,010 m en cada 500m** (comparación numérica). **Esto NO prueba exactitud milimétrica de edificios, árbol, relieve o fachadas**, ni datum vertical.
- Botón A/B dentro del visor local: alternar entre el mundo 3D original archivado y OSM/PNOA, sin reiniciar sesión ni perder controles del juego. El archivo original no se transmite al repositorio.
- `render_worldmaster_cpu.py` hace reproducible un render técnico con verificación del SHA de cada GLB, sin prometer fotorrealismo.

**QA separado por naturaleza:** pruebas Python de fuente y pipeline con fixtures; Node+Three comprueba mallas reales sintéticas, poses, budget, proyección y máscaras de material; Chromium de GitHub valida el visor público sin archivos de Drive. Chromium local en este entorno devolvió `net::ERR_BLOCKED_BY_ADMINISTRATOR`, por lo que queda expresamente pendiente validar el conjunto real de 75 GLB en Windows. No atribuir la restricción del navegador al código de NeuroCity.

**Lote v2 local:** regenerado para propietario a partir del mismo ZIP fuente original, incorporando `game.js` compilado por CI, SHA-256 intacto de los 75 GLB, nueva metadata y documentos de QA. No fusionado, no desplegado, no distribuido públicamente por GitHub.

## Consolidación verificable posterior (20/10/2026) · PR #53 → #54

**Autoridad única de código y fuente abierta:** `clucaina/NPL-CANONICAL`. Esta sección ACTUALIZA el avance histórico de 75 GLB: la cadena privada G19/V50 más reciente de PR #51/#52 describe 86 GLB y 88 referencias, sin mover bytes al repositorio; no equiparar números de versiones diferentes. **PR #53** conserva máscaras arquitectónicas por triángulo cargado y evita ocultar OSM por cuadrados enteros de 500 m. **PR #54** añade geodatos reales y licencia (ambas en borrador, sin merge ni deploy).

**Archivo único privado en Drive:** `NeuroCity/CONTROL_CANONICO_GITHUB/` contiene auditorías y candidatos derivados públicos, NO el traslado de toda la carpeta de producción ni avatares privados. Los paquetes propietarios originales permanecen donde estaban; GitHub solo publica fuente y metadatos auditables. Esto evita copiar 100 MB por versión o abrir permisos nuevos.

### Recuperación cruzada sin repeticiones
- Historial Geo G12 del propio Drive comprobado: `r01_c02`, bbox UTM (720700,4247300,721200,4247800), error anterior `DOWNLOAD_OR_VALIDATION_FAILED`, `NO_RASTERS_READ`. **No era una elevación real**.
- Geo G19, Gameplay G15.1/G16 y archivo G19/V50 preservados, sin importar ni publicar binarios propietarios.
- v20 Base + v20 Arquitectura en Drive, CRC intacto; v20 contiene PBR experimental de Explanada y **alzado hipotético** de Casa Carbonell. No equivale a la malla propietaria G14 ni reemplaza PR #45.
- Catálogo Kenney propietario `CATALOGO_KENNEY_1883_LOCALIZADOS.json`: 1.883 entradas, sin SHA256 de binario. Se conserva como `located_only`, no como 1.883 modelos importados. Mirror GitHub del repositorio declara licencia SPDX `NOASSERTION`; validar derechos de cada archivo antes de usar. Los modelos G19 existentes se reutilizan con prioridad.
- Huerto `cloud_factory/neurohuerto_architecture.json` solo certifica **15** IDs públicos. No declarar integración automática de las 26 raíces sin inventario contrastable; solo intercambiar metadatos, no clientes ni activos privados.
- NPL y Conflictómetro permanecen por contratos públicos existentes; ni una base ni un paciente se han copiado a este proceso.

### Terreno oficial Alicante r01_c02 obtenido por fin

Fuente documental original: [IGN/CNIG MDT05](https://api-coverages.idee.es/collections/EL.ElevationGridCoverage_25830_5_PB?f=json), [productos PNOA-LiDAR](https://pnoa.ign.es/pnoa-lidar/productos-a-descarga), reutilización CC BY 4.0 (atribución obligatoria). Esta colección es un **MDT5 de primera cobertura**, NO un LiDAR 2025 de 5 puntos/m2 ni fotogrametría. La fuente devuelve TIFF en `EPSG:3042`, ETRS89/UTM 30 N-E, que se normaliza a `EPSG:25830` E-N sólo tras cinco controles `pyproj.Transformer(..., always_xy=True)` de igualdad X,Y (<0,1m). En la prueba GitHub Actions [39465916862](https://github.com/clucaina/NPL-CANONICAL/actions/runs/39465916862), **SUCCESS** en dos jobs: 12 tests licencia, 7 tests raster y 5 tests GLB; descarga real y 3 LOD.

- Fuente COG `daca80a6b61277e40bfcccadcdd306fa1730b90272ae2fe99f858291af2d82e5` (SHA256), matriz 101×101, 10.000 píxeles válidos (98,03%), elevaciones observadas 0 a 34,016 m.
- LOD0 (5 m): **10.000 vértices, 19.602 triángulos, 476.772 bytes**; SHA256 `50b008c887a6ee7b12ce5ca5c522276f244d87fb38e018c518bc8d93f79550a4`.
- LOD1 (10 m): **2.500 vértices, 4.802 triángulos, 119.164 bytes**; SHA256 `2732eb391bcefa6c6c0dbda645e13ca03b51d8a26861ebeffbd6c80dde3e8a4f`.
- LOD2 (20 m): **625 vértices, 1.152 triángulos, 30.360 bytes**; SHA256 `19817c6d33ef08a1769ce63cbfba1d0392a42dd85f9ce007a58e0be691859585`.
- Se han verificado CRC ZIP y cabecera GLB 2.0 mediante lectura limpia; los tres están archivados en la carpeta privada de control, bajo atribución: *Obra derivada del MDT05 (primera cobertura LiDAR) - IGN/CNIG, CC-BY 4.0 scne.es*.
- **NO** se ha aplicado ese relieve al Gameplay: datum vertical local y correspondencia de cotas con G19/V50/edificios/cimientos aún no validados; no es fotorrealismo ni FPS real.

### Recursos abiertos complementarios (sin descarga masiva)

`tools/neurocity/public_free_sources_20261020.json` registra 11 fuentes/tecnologías con herramienta ejecutable `source_admission.py` y pipeline `neurocity-source-admission-qa.yml`. Incluye Kenney CC0 original, Poly Haven CC0 (API tiene ToS separada), IGN/CNIG CC-BY 4.0, glTF-Transform MIT, NASA 3DTilesRendererJS Apache 2.0, QGIS GPL-2.0 (herramienta offline) y PDAL/mirror Kenney sujetos a revisión de licencia. **0 activos nuevos de terceros insertados en mundo G19**: catálogo `located_only` no es geometría real.

### Bloqueos que NO se declaran resueltos

(1) Contrastar cotas MDT05 vs referencia vertical real del sistema G19/V50 y navegación; (2) integración Catastro/agua/G19 PR #49: seis conflictos sin merge, no borrar mejoras anteriores; (3) escenarios LiDAR más recientes y fachadas reales requieren archivos y procedencia precisos; (4) integración controladores/avatares G16 sin duplicar lógica; (5) E2E WebGL privado, FPS GPU y aprobación visual de Alicante. Un artefacto generado exitosamente no equivale a una ciudad jugable terminada.
