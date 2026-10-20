# NeuroCity — Casa Carbonell G14 · mejora privada L2

Intervención material aditiva sobre el GLB original G14 de Casa Carbonell en el mundo maestro G19/V50. No se ha creado una ciudad paralela ni se ha sustituido la base por footprints OSM.

## Fuente auténtica y anclaje
- Paquete propietario V7 SHA256: 75fbe60079c0f02c4c0d9263ed8803a4882b95402dda4345c21d883fe2090775.
- GLB G14 original: world-master/assets/source/ASSETS/G14/G14_historic_carbonell_244990.glb. SHA256 ceb9728f29ebe402ae1a4c7dda63790f67ab2985d6df7837bf31146caa8c5ece, 863.152 bytes, 9 mallas, 42.865 triángulos y 9 materiales PBR.
- Catálogo oficial municipal Casa Carbonell C48, Explanada 2, referencia catastral 0272901YH2407A, coordenadas publicadas X=720147 Y=4247038: https://www.alicante.es/sites/default/files/documentos/noticias/informacion-publica-del-catalogo-protecciones/patrimonio-cultural-2-birl-integralr-c40-c97.pdf .
- Centro de GLB maestro X=447,14 Z=1262,14 compatible con anclaje local UTM [447,1262], residuo 0,20 m. Esto NO mide exactitud del edificio ni asegura que el punto oficial sea el centro real.
- G13 physical_r02_c00: altura local centro 2,071 m; mínimo Y de malla G14 2,0805 m. Residuo local 0,0095 m; NO altura oficial ni datum verificado.

## Modificación real
GLB L2 propietario G14_CASA_CARBONELL_SOURCE_PRESERVED_L2_PRIVATE.glb SHA256 ac82b798d5bc9cc0680f25d4325e94f65622bd8d0989a809dc7474c43931c678, 1.126.780 bytes, 11 mallas, 56.305 triángulos. Las 9 mallas originales conservan VÉRTICES y CARAS idénticos. Se agregan nervios curvos a las dos cúpulas G14 y finos montantes 3D a los 272 componentes acristalados de G14 original. Ornamentación INTERPRETATIVA y no levantada: la forma exacta de los ornamentos NO está certificada.

Referencias fotográficas de comparación, sin incorporar imágenes de terceros al GLB: https://commons.wikimedia.org/wiki/File:Alicante_Casa_Carbonell_05.jpg (Oilisab, CC BY-SA 4.0); https://commons.wikimedia.org/wiki/File:Casa_Carbonell_de_Alicante.jpg (CC BY-SA 3.0; autor en ficha Commons).

## Sustitución reversible y testada
El script tools/neurocity/apply_carbonell_l2_owner.py comprueba hashes exactos, preserva 177 ficheros originales del ZIP, modifica únicamente el manifiesto V50 y agrega un activo seleccionado. Sustituye UNA referencia landmark en r02_c00 y conserva el GLB antiguo como respaldo SIN duplicar edificios en el visor. Candidato ZIP original+overlay validado: CRC PASS y equivalencia SHA de 177 integrantes. La ejecución de glTF2 pasó parsing independiente y comprobación estructural (11 meshes/materiales y 22 accessors/bufferViews), pero NO el validador oficial Khronos.

Pendientes: Chrome/WebGL original bloqueado por ERR_BLOCKED_BY_ADMINISTRATOR; NO FPS/memoria móvil, NO comparación 1:1 aprobada con foto, NO altura vertical certificada, NO validación física ni revisión humana. Las capturas actuales son RENDERS CPU VTK del propio GLB, no juego WebGL. Prohibidos merge/deploy/costes, publicación del GLB o ZIP propietario, personajes/empleados/rótulos inventados.

Grafo canónico: esta rama desciende directamente de PR #43 → PR #40 V7, con colisiones provenientes de PR #39. PR #42 usa suelo local Y=0 por defecto; NO trasladar directamente a G19 donde terreno local Casa Carbonell es ≈2,07 m, sin adaptar G13 por posición. No tocar Gameplay de personajes, vehículos, cámara, NPL/Conflictómetro ni fuentes privadas.
