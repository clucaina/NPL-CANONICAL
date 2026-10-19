# NeuroCity · catálogo 3D libre y política de realismo (19/10/2026)

## Qué se ha creado
El visor público incorpora un kit paramétrico original de palmeras mediterráneas, bancos, maceteros y aparcabicicletas, con geometría real Three.js, materiales físicos estándar e instanciación en 9 grupos de dibujo. Se modelan procedimentalmente, no son fotografías ni reproducciones exactas de bienes arquitectónicos. Se conserva la base OSM/PNOA. El número de polígonos y la visibilidad se comprueban en las pruebas de CI.

**Nunca:** insertar edificios de catálogo sobre edificios georreferenciados para simular que son Alicante, atribuir ubicación exacta a objetos artísticos, incorporar mallas humanas privadas, publicar bases clínicas o archivos originales de NPL/Conflictómetro. Un kit CC0 no implica fidelidad cartográfica, ni fotorrealismo.

## Fuentes libres concretas que deben integrarse solo tras auditoría de contenido

| Recurso verificado | Formatos / volumen declarado | Licencia publicada | Uso estratégico | Estado |
| --- | --- | --- | --- | --- |
| [Kenney Nature Kit](https://kenney.nl/assets/nature-kit) | 330 archivos 3D | CC0 | Vegetación variada de relleno; estética simplificada, no botánica fotografiada | Identificado, **no importado** |
| [Kenney City Kit Roads](https://kenney.nl/assets/city-kit-roads) | 90 archivos 3D | CC0 | Señalización, barreras, semáforos; correspondencia con OSM pendiente | Identificado, **no importado** |
| [Kenney City Kit Commercial](https://kenney.nl/assets/city-kit-commercial) | 50 archivos 3D | CC0 | Prototipado urbano solo en sandbox, NO edificios reales de Alicante | Identificado, **no importado** |
| [Kenney City Kit Suburban](https://kenney.nl/assets/city-kit-suburban) | 40 archivos 3D | CC0 | Laboratorio de estilización, no reconstrucción geográfica | Identificado, **no importado** |
| [Kenney City Kit Industrial](https://kenney.nl/assets/city-kit-industrial) | 40 archivos 3D | CC0 | Entornos sintéticos segregados | Identificado, **no importado** |
| [Kenney Car Kit](https://kenney.nl/assets/car-kit) | 45 archivos 3D | CC0 | Vehículos decorativos no asociados a personas reales | Identificado, **no importado** |
| [Kenney Building Kit](https://kenney.nl/assets/building-kit) | 80 archivos 3D | CC0 | Componentes editables, edificios no georreferenciados | Identificado, **no importado** |
| [Poly Haven](https://polyhaven.com/af/our-api) | API /assets?t=models; no total certificado | CC0 de activos; condiciones propias para API | Activos PBR, plantas, mobiliario, HDRI, catálogos revisables | Colector de **metadatos**, sin binarios |
| [Blender](https://www.blender.org/about/) | Suite open source GPL | GPL software | Retopología, Geometry Nodes, atlas UV, LOD y exportación glTF | Pipeline abierto disponible |

Los 675 archivos **declarados** por Kenney en esos siete paquetes no se han descargado ni verificado individualmente; no constituyen 675 objetos ya colocados. Las cantidades publicadas pueden variar. CC0 no garantiza calidad o idoneidad para un barrio concreto.

## Sistema de decisión visual
1. **Geometría real:** mantener polígonos OSM/levantamientos oficiales en su sistema de referencia; alturas no inferidas como medidas.
2. **Aumento visual:** PBR y mapas normales reales con resolución <=1K móvil / <=2K PC; usar KTX2/BasisU tras verificación.
3. **Instancias y LOD:** repetir geometría con InstancedMesh; perfiles mobile/desktop, límites de triángulos y sombras. Poly Haven modelos de millones de tris requieren retopología, NO render directo en web.
4. **Distribución veraz:** vegetación/bancos puramente decorativos con indicador “posición ilustrativa”; objetos con ubicación demostrada requieren ID de fuente y precisión espacial.
5. **Evidencia:** navegador Chrome/Firefox/WebGL, capturas antes/después, FPS p50/p95 en dispositivo real, bytes GLB, draw calls y volumen visible.
6. **Controles:** catálogos externos nunca cargan JS de terceros; archivos GLB nuevos se revisan, convierten offline, validan hashes y licencias por archivo.
7. **Datos NPL y Conflictómetro:** sólo agregados con contrato versionado y procedencia verificable, NO fotografías/personas o localizaciones sensibles. Se mantienen inalterados los originales.

## Descubrimiento masivo sin descargas ciegas
`python3 tools/neurocity/curate_cc0_assets.py --live --limit 120 --output /tmp/cc0_candidates.json`.
El comando consulta el listado público de **metadatos** de modelos de Poly Haven, selecciona hasta 120 candidatos relevantes, descarta futuros y nombres inseguros y guarda fichas URL/licencia. NO descarga ni coloca modelos. Ejecutar en GitHub Actions genera artefacto revisable sin añadir binarios al repositorio. Si falla la API por límites o disponibilidad, conservar el fallo y no inventar resultados.

## Bloqueos aún reales
- El acceso a archivos originales reales del Conflictómetro y de NPL no equivale a contratos exportados: aún falta validación de ingestión de fuentes públicas oficiales.
- Calidad visual actual es estilizada; no es un gemelo digital de Alicante, y las ubicaciones de bancos/palmeras son ilustrativas.
- No se ha demostrado objetivo de 60 FPS sostenidos ni menor gasto energético en hardware móvil; Chromium con renderizado software sirve para integridad funcional, no para rendimiento.
- No cargar **automáticamente** archivos 3D de proveedores externos en la web: metadatos y archivos requieren revisión de geometría/licencia/atribuciones.

## Auditoría de binarios de Poly Haven (ejecución del 19/10/2026)
Los tres slugs públicos examinados (`street_lamp_01`, `modular_street_seating`, `painted_wooden_bench`) sí exponen `.gltf` + `.bin` y `.blend`, pero **no** variantes GLB directas bajo 16 MB. El servicio entregó `.blend` con envoltorio Zstandard (magic `28b52ffd`) y longitud comprimida coincidente con su metadato.

Tras descodificar, los tres archivos recibidos tenían exactamente **35.572 bytes** cada uno y cabeceras Blender, **pero carecían de los bloques estructurales `DNA1` y `ENDB`**: por tanto NO pueden certificarse como fuentes Blender completas ni promocionarse como modelos 3D importados. El validador actualizado los rechaza. Puede tratarse de una respuesta corrupta/incompleta en esta ruta de transferencia; no se atribuye el fallo necesariamente al proveedor ni a su colección original.

**Acción siguiente:** inspeccionar variantes `.gltf` y dependencias `.bin` con validación de accesores/primitivas y comprobación de hash, o convertir directamente paquetes oficiales ya completos en un entorno Blender aislado con ejecución automática de scripts deshabilitada. Ningún modelo externo se introduce en la escena OSM hasta superar carga, integridad, licencias, triángulos, materiales y revisión visual.
