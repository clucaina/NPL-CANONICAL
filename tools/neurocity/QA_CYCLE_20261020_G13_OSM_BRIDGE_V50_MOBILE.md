# NeuroCity V7 · ciclo material de continuidad G13/G19/V50 · 2026-10-20

**Fuente base:** PR #46, SHA `093b94856eced23ec640b629780bd55d67ebb631`, sobre PR #45 → #43 → #40; colisión inicial PR #39; materiales privados G19/V50 **NO** subidos, borrados, reconstruidos ni alterados.

**Evidencia CI previa (PR #46):** GitHub Actions bundle y playable_review en Chromium públicos SUCCESS en SHA de base; NO implica WebGL privado, fidelidad arquitectónica o FPS móvil.

## Defecto corregido A — huecos de cobertura en el atlas físico G13

Archivo fuente: `demos/npl-world/visual_viewer/world_physics.mjs` y llamada real desde `app.js`.
- Antes: `RecoveredPhysicalAtlas.move` trataba `canOccupy().allowed===null` como movimiento libre aunque `cityCollision` ya tuviese paredes reales extraídas del GLB público. Una celda G13 no disponible permitía atravesar dichas paredes.
- Ahora: callback síncrono `fallbackCollision` consulta el barrido continuo original de la PR #46, **solo en casillas G13 sin cobertura**. `allowed===false` prevalece y bloquea; `allowed===true` prevalece; ninguna decisión G13 comprobada es reemplazada por OSM.
- Sin geometría de paredes, se conserva la navegación provisional pero se expone `unverifiedFallbackSubsteps` en QA. Se cuentan también consultas y bloqueos reales del fallback. No hay barreras, rutas, locales ni obstáculos inventados.
- Seis pruebas Node integran el `RecoveredPhysicalAtlas` con una malla de pared Three.js sintética, el recorrido, un deslizamiento, las prioridades G13 y el rechazo de respuestas inválidas. NO usar esas mallas de prueba como prueba fotogramétrica.

## Integración de otro chat — PR #35 a V7, sin repetir el desarrollo

El archivo `city_tiles.mjs` de V7 todavía permitía que capas obligatorias `terrain/geo/architecture/mosaic` **eludieran el presupuesto móvil** de 290.000 triángulos o 30 imágenes estimadas.

Se ha portado, sin reescribirlo, el control ya implementado en PR #35 `feat/neurocity-v50-source-surgical-lod-20261020`: todas las capas móviles respetan el techo estimado. Se conserva la selección verificada de V50 PBR original como fallback de 5.225 triángulos frente al candidato físico de 105.345 triángulos. Si una capa crítica supera el presupuesto, queda sin cargar y se utiliza el fallback geográfico previo; **no equivale a terreno jugable recuperado**.

Cuatro pruebas Node verifican que una capa obligatoria no supere límites, que V50 original prevalezca en móvil, que desktop permanezca igual y que un escenario insuficiente no se declare cargado.

## Evidencia exacta

- SHA de implementación probada: `9ca73706f77e27a59cd4e995b7191902c8656bbd`.
- GitHub Actions: https://github.com/clucaina/NPL-CANONICAL/actions/runs/39436136753/job/118673542482 — **SUCCESS**, `node --test tests/*.test.mjs` **89 tests PASS / 0 FAIL**, `npm run build` PASS. El recuento incluye pruebas preexistentes, **10 nuevos casos** en esta rama.
- SHA anterior de integración G13 aislada `718f6e2d20b8828a04ac6ebf6c89de0d2a87af54`: CI SUCCESS, 85/85 pruebas, https://github.com/clucaina/NPL-CANONICAL/actions/runs/39435965205/job/118672923740.
- Rutas nuevas: `demos/npl-world/visual_viewer/tests/g13_g19_wall_fallback.test.mjs`, `demos/npl-world/visual_viewer/tests/v7_mobile_budget_port.test.mjs`.
- Rutas modificadas: `app.js`, `world_physics.mjs`, `city_tiles.mjs` bajo `demos/npl-world/visual_viewer/`.

## Límites de aceptación y próximo bloqueo

**NO SE HA CONSTRUIDO OTRO EDIFICIO** ni se han contado footprints como fachadas. Sin cambio de fuentes históricas privadas ni contratos NPL/Conflictómetro. Sin merge, deploy, costes, pacientes, personas identificables o recursos comerciales.

El éxito del runner es prueba de lógica TypeScript/JavaScript, compilación y contratos aislados. Faltan: ejecutar y capturar WebGL privado con G19/V50/G13 firmados; comprobar las rutas de caída a OSM en el juego completo; comparación 1:1 de fachadas reales; contrastar alturas con LiDAR/MDT y datum vertical; FPS/VRAM en Intel y móvil físico. Las métricas del LOD son **estimaciones por manifiesto**, no GPU medida. El fallback G13 sin OSM visible sigue explícitamente sin certificar.

**Siguiente intervención distinta** (si hay datos reales): comprobar continuidad de colisiones en borde de teselas G13 y evitar doble carga 3D al cambiar del atlas público al archivo G19, solo tras pruebas de cámara/render auténticas. No intervenir nuevamente Casa Carbonell.
