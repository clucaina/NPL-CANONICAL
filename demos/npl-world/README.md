# NPL WORLD — Alicante · Modo georreferenciado (10 octubre 2026)

**Juego HTML publicado:** [Abrir Alicante geográfico 3D](https://raw.githack.com/clucaina/NPL-CANONICAL/main/demos/npl-world/index.html)

**Modo experimental fotogramétrico:** [Abrir Alicante Google Photorealistic 3D Tiles](https://raw.githack.com/clucaina/NPL-CANONICAL/main/demos/npl-world/alicante_fotogrametria.html) — precisa clave propia de Map Tiles API, conexión, cobertura y condiciones de facturación. No incluye una clave ni la almacena.

## Funciones implementadas
- Georreferenciación de Alicante mediante OpenFreeMap y OpenStreetMap.
- Edificios extruidos a partir de huellas y alturas de datos cartográficos disponibles, sin fachadas fotográficas. Opción de capa aérea Esri con atribución y términos de uso del proveedor.
- Control WASD, carrera con Mayús, orientación con ← →, cambio de vista con V, cámara con seguimiento, cinco hitos geolocalizados, interacción E con distancia de 25 metros.
- Adaptador Three.js/GLTFLoader para cargar un humano femenino skinned CC0 de Innerscene MakeHuman con siete animaciones embebidas (Idle/Walk/Run), y opción para importar otro GLB con los clips requeridos.
- El humano conserva tamaño de 1,67 metros y orienta el cuerpo en dirección del movimiento. Se rechazan clips sin locomoción completa en lugar de dejar una T-pose con apariencia de funcionamiento.

## Límites y verificación
No existe todavía modelo facial de Lucía derivado de referencias originales, ni ciudad GTA fotorrealista, ni colisiones urbanas, ni tráfico simulado a escala, ni interior de edificios. Datos geográficos reales **no equivalen** a fotogrametría. Imágenes satelitales **no equivalen** a fachadas texturizadas.

Se comprobó sintaxis JS con Node y la lógica de entrada, WASD, hitos, alternancia de satélite, cámara y reinicio con Playwright **simulando los proveedores externos**; no se verificaron GPU, el WebGL real, el GLB remoto ni FPS en navegador conectado. La carga de modelos depende de Internet y permisos CORS del proveedor.

La escena low-poly anterior permanece archivada en [escena_lowpoly_archivada.html](escena_lowpoly_archivada.html) y ya no es el inicio del juego.
