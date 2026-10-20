# NeuroCity V8 · recuperación entre chats, máscara arquitectónica REAL y continuidad

Fecha: 2026-10-20. Base exacta G19/V8 preexistente: `2e4d9b650f5335e7669908985a804986e0a119a5`; no parte de `main`. Rama aislada: `fix/neurocity-v8-geometry-cover-and-avatar-lineage-20261020`.

## Auditoría antes de editar — qué NO se repitió

- PR #39/#41/#46/#50: barrido continuo, prueba de paredes y prioridad G13 ya existentes.
- PR #31/#35/#40: mosaico V50 PBR y LOD; atlas cerebral NPL original 437 estructuras / 563 primitivas: no tocados.
- PR #44/#51: 86 GLB propietarios y ensamblado owner-only: no modificados ni publicados.
- PR #29/#38/#52: mar, Catastro real experimental 207 building parts, ajustes de shaders y render/streaming: no reimplementados.
- PR #47/#48/#52: render adaptativo, cola global acotada, fallback de colisiones G13 y presupuesto de triángulos: conservados.
- PR #49: CROSS_CHAT_LINEAGE y workflow de convergencia están solo en su rama borrador, NO en `main`.
- `main` SHA `db4d1e53886f9769c3dd6535a8e7918b428bffa6`; ejecución de convergencia `39439431338` FAILURE. El informe adjunto confirma dos conflictos en integración GEO (`city_tiles.mjs`, `water_surface.mjs`) y seis con Catastro/browser (`app.js`, `city_tiles.mjs`, `browser_public_review.mjs`, `water_surface.test.mjs`, `water_surface.mjs`, `world_master_loader.mjs`). Esos merges no están aprobados ni ensayados conjuntamente.
- Huerto `cloud_factory/neurohuerto_architecture.json` en `main` es `METADATA_ONLY_NO_CLIENT_FILES` con 15 IDs verificables: **NO declara las 26 raíces** hasta que exista su inventario firmado. NPL/Conflictómetro, bases y pacientes permanecen fuera del proyecto.

## Defecto geométrico nuevo — regresión de ocultación masiva

El shader de `osm_building_mask.mjs` descartaba **todos los fragmentos OSM** cuyo X/Z cayera dentro de una caja de tesela G19 de 500×500m. Una tesela puede tener una malla `architecture.glb` compuesta por centenares de edificios separados y zonas vacías. `onCoverage` podía marcar el cuadrado entero aun cuando su cobertura construida fuera mínima. El selector de comparación también usaba `status().tiles` sin discriminar geometría.

### Construcción implementada en esta rama

- `g19_architecture_coverage.mjs` recorre solo triángulos de geometría **firmada, cargada y visible** bajo `MASTER_architecture`, aplica su transformación de tesela y rasteriza su ocupación proyectada X/Z a rejilla de 256² (~1,95 m/celda). Los muros verticales proyectados se dibujan como segmentos. Extiende una celda para no dejar huecos por proyección aproximada. Sin datos reales no genera ninguna máscara.
- `osm_building_mask.mjs` aloja cuatro rejillas en un solo atlas `DataTexture` de 512² RGBA (1 MiB) y limita el `discard` a los píxeles realmente ocupados. **Nunca** usa el cuadrado completo como prueba de presencia. Terreno PNOA, asfalto y agua no se recortan.
- `world_master_loader.mjs` entrega solo máscaras de arquitectura cuya geometría está cargada y verificable; descarta mapas de 0 triángulos y no resuelve fallos de detalle como si fueran ausencia de arquitectura. Cachea cada raster y deja de transmitir cobertura de tesela indiscriminada.
- `app.js` conecta tanto el streaming como el selector manual OSM/G19 a este mismo criterio. Al desactivar el mundo original, la máscara queda vacía y se muestra la fuente OSM.
- Cinco pruebas Node específicas verifican cobertura pequeña, ausencia de geometría, errores, inyección de shader y rechazo de máscaras alteradas.

### Auditoría geométrica offline propietaria sin redistribución

Con los auténticos GLB archivados G19/V50 y trimesh/Pillow, se obtuvieron estas estimaciones de superficie representada dentro de cuatro teselas de 500m:

| Tesela | Meshes | Triángulos originales | Píxeles geométricos cubiertos, tras 1 celda de expansión | Área de OSM que antes podía descartarse sin arquitectura |
|---|---:|---:|---:|---:|
| r02_c00 | 291 | 148554 | 54,58% | 45,42% |
| r02_c01 | 150 | 144514 | 16,38% | 83,62% |
| r01_c01 | 67 | 17672 | 7,20% | 92,80% |
| r01_c02 | 22 | 420 | 3,80% | 96,20% |

Los valores son cobertura raster CPU de triángulos archivados, **NO superficie urbana edificada real certificada, no altimetría LiDAR, no fotorrealismo ni capturas WebGL**. Las imágenes y hashes privados quedan en la entrega local del propietario, no en el repositorio público.

**QA del código**: SHA `dfd5538b38e09a1d326c4c80bebe2d345ff18db6`, Actions `39461425251` **119/119 Node PASS**, build esbuild PASS. El Chromium público y la ejecución de archivo propietario quedan sujetos a su check independiente; no anticipar resultado.

## Chat de avatares recuperado; evitar sobrescritura

Se autenticaron en la cuenta Drive propietaria, descargaron y verificaron CRC+SHA los ZIP históricos:
- G08 incremental Rocketbox: 25 ficheros, cinco modelos GLB originales.
- G15.1 completo corregido: 257 archivos.
- G16 candidato: 270 archivos; comparación **245 byte idénticos**, 12 modificados, 13 añadidos, sin archivo perdido. Incluye sistema de flota, personas, asientos, contacto, Fufú, animación, agua, cámara y vehículos.
- Original G19/V50 V7 de Biblioteca: 178 miembros, 86 GLB / 88 referencias archivadas según sus propios contratos. **No equivale al mismo motor ni al avatar anterior**.

La entrega **solo privada** `NEUROCITY_AVATAR_RECOVERY_G16_DELTA_PRIVATE.zip` incorpora los 25 ficheros nuevos/modificados de G16 y cinco variantes históricas separadas de G08; reconstrucción completa exacta de G16 desde G15.1 probada SHA-a-SHA. **No se incluye el paquete ni ninguna malla privada en GitHub**. El propietario conserva sus ZIP originales.

Pruebas genuinas sobre G16 extraído en staging privado: `QA_G15_2_CONTROLLERS.node.js` 29/29 PASS y `QA_G16_FLEET.node.js` 12/12 PASS (entorno de lógica/mocks). **WebGL V8/G16 combinado no probado**, identidad y apariencia de avatar sin certificar, modelos G16 simples no son calidad AAA. Rocketbox MIT, Fufú CC BY 4.0 con atribución, CMU y otras licencias por recurso; sin publicar por defecto.

## Bloqueos abiertos para aceptación, no inventar éxito

1. Chromium público del último SHA y prueba de máscaras de *GLB privado en el navegador real*. Node y CPU no son WebGL ni FPS móvil.
2. Resolver conflictos G19/Catastro PR #49 en rama integradora aparte; no sobrescribir agua/collision/LOD a ciegas.
3. Integrar motores históricos G16 con propietario de control único y estados coherentes: NPC, tráfico, Fufú, conducción, asientos y animación tienen que pasar pruebas de escena y compatibilidad, no copiar `game.js` antiguo.
4. Obtener fotos utilizables con licencia y MDT/LiDAR con datum vertical contrastado por tesela antes de certificar fachadas/cotas.
5. Rendimiento de GPU Intel/móvil real, memoria, VRAM y aceptación humana.
6. Nunca fusionar/desplegar/provocar costes ni exponer recursos privados o pacientes sin autorización específica.

Este PR no publica modelos ni toca datos NPL/Conflictómetro, y conserva gobernanza metadata-only del Huerto.
