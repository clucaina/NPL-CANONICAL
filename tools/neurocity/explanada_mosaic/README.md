# NeuroCity · Explanada de España · teselas 3D reales (CANDIDATO, sin integrar)

**Es geometría realmente construida, no un recuento de edificios:** el archivo `explanada_4x4m_near_real_geometry.glb` contiene **10.000 teselas de mármol de aproximadamente 4 × 4 cm modeladas individualmente** (top y cuatro cantos físicos por pieza), sobre plano independiente de mortero. Las piezas tienen una ligera variación de altura interpretativa de menos de 0,5 mm; **100.000 triángulos de mármol**. El GLB lejano usa **dos triángulos y textura PBR** generada desde la misma paleta para distancia / móvil. Ambos son modelos 3D reales en formato glTF 2.0.

Fuentes del **material y tamaño**: [Universidad de Alicante (guía geológica, p. 37)](https://web.ua.es/es/actualidad-universitaria/documentos/docs-anteriores/2020/noviembre2020/ruta-geologica-alicante.pdf), [Turismo Alicante](https://alicanteturismo.com/jardines/la-explanada-de-espana/), [Alicante Film Office](https://www.alicantefilmoffice.com/localizacion/explanada-espana/). Fuentes municipales citan 6,6 millones de teselas para todo el paseo, no para nuestro parche. El dibujo real es ondulante en tonos crema/rojizos/oscuros. No se ha copiado ni redistribuido ninguna imagen de terceros.

## Honestidad geométrica

- **Medido/publicado**: escala aproximada de cada tesela (4 × 4 cm), tres familias de piedra, patrón ondulante.
- **Reconstrucción artística, NO levantamiento**: amplitud/fase/período del patrón, tonos exactos RGB, junta de 1,1 mm, desniveles y colocación individual de cada piedra. **No afirmar similitud milimétrica**.
- **Sin coordenada autorizada de colocación**: **4 m × 4 m = 16 m²**, origen local (0,0,0); ni latitud, ni cota G05. El G19/V50 original no se sustituye; falta identificar el tramo correspondiente y medir anclaje EPSG:25830/vertical.
- **Sin WebGL de juego verificado**: 8 tests Python de lectura GLB/triángulos/materiales/SHA/repetición y un test Node de cambio LOD; ninguna cifra FPS/triángulos visibles por GPU real.

## Archivos e integración

`build_mosaic.py` crea ambos GLB y textura. `asset/mosaic_manifest.json` conserva SHA y límites. `local_mosaic_lod.mjs` permite probar alternancia opcional en escena Three.js con `GLTFLoader`, y **rechaza integración en mundo real si no hay coordenadas/cota validadas**. Sólo `preview:true` admite origen sintético. No modifica `game.js`, `world_physics.mjs`, `world_master_loader.mjs`, NPL ni Conflictómetro. Para integrarlo, medir anclaje real y recortar/sustituir el parche mosaico existente **sin suelo duplicado ni z-fighting**; conservar colisiones y navegación histórica G13.

## Regeneración y tests

```bash
python -m pip install numpy pillow trimesh
python build_mosaic.py --out asset --texture-pixels 2400
python -m unittest discover -s . -p test_mosaic.py -v
node test_mosaic_lod.mjs
```

**Aceptación pendiente**: incorporar activos bajo ruta local propietaria, capturar Chromium WebGL en el Gameplay ORIGINAL sin sustituir G19, comparar el mismo punto de vista con fotos autorizadas, revisar mosaico, palmeras y fachadas contiguas y medir frametime móvil/escritorio. Sólo después pasar de *candidato 3D* a *integración jugable verificada*. Sin despliegue y sin gastos.