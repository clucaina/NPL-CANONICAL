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
