# NeuroCity — bloqueo de integración entre chats, 20/10/2026

**Estado:** conflicto REAL reproducido en runner de GitHub, no una hipótesis narrativa. No hacer merges sobre `main` ni desplegar.

## Fuentes actuales y procedencia

- Línea original G19/V50/V7 y Casa Carbonell G14, con colisión de barrido continuo: [PR #46](https://github.com/clucaina/NPL-CANONICAL/pull/46), fuente `093b94856eced23ec640b629780bd55d67ebb631`.
- Ciudad reconstruida con 207 partes 3D oficiales Catastro (38 edificios OSM emparejados + 52 partes nuevas), ensayo WebGL y prueba física: [PR #41](https://github.com/clucaina/NPL-CANONICAL/pull/41), fuente `903df0e0d071ce6a5de095344edf3ab9564cbfac`. Este contrato no sustituye G19/V50 ni el cerebro NPL auténtico.
- Ensayo independiente de fuentes: [PR #38](https://github.com/clucaina/NPL-CANONICAL/pull/38), fuente `b7ba277aa0983ec4559c632cd789d70ca5890e16`.
- Ensamblador local privado G19/V50: [PR #44](https://github.com/clucaina/NPL-CANONICAL/pull/44), fuente `004e19a66cf8c015a05178740941538dd71965a7`. Consultar código, nunca copiar los GLB privados a repositorios públicos.
- Huerto y automatización recurrente: rama `main` `99c75a90a413139159cc542c3615d8931c084a9d`. Los datos originales NPL/Conflictómetro permanecen aislados.

### Bloqueo reproducido

El job GitHub Actions **39436363446** hizo merges temporales de las ramas actuales, sin fusionar producción:

- Catastro / aceptación sobre G19/V50, seis conflictos:
  - `demos/npl-world/visual_viewer/app.js`
  - `demos/npl-world/visual_viewer/city_collision.mjs`
  - `demos/npl-world/visual_viewer/city_tiles.mjs`
  - `demos/npl-world/visual_viewer/tests/city_collision.test.mjs`
  - `demos/npl-world/visual_viewer/water_surface.mjs`
  - `demos/npl-world/visual_viewer/tests/water_surface.test.mjs`
- Ensayo de fuentes adicional: `demos/npl-world/visual_viewer/city_tiles.mjs`.

**Resultado del ensayo:** pruebas independientes G19/V50 PASS; merge combinado BLOQUEADO y compilación conjunta NO TESTEADA. El workflow corregido termina con un error explícito; un check verde anterior no equivalía a fuente unificada.

### Resolución necesaria sin perder módulos

1. **app.js**: utilizar G19/V50 como propietario de la ciudad original y del cerebro anatómico NPL. Injertar solo el puente aprobado de GLB catastral y sus pruebas de privacidad, manteniendo escenas y contratos educativos existentes. No reconstruir ni sustituir los 437 nodos originales por un cerebro de demostración.
2. **city_collision.mjs**: preservar el barrido continuo de PR #46, añadir las comprobaciones de aceptación de PR #41 sin volver al algoritmo solo por extremos y mantener prioridad del atlas G13 cuando está verificado.
3. **city_tiles.mjs**: compatibilizar fuentes geográficas históricas y política de presupuesto de GLB del otro desarrollo; comprobar la misma malla georreferenciada y fallback OSM cuando faltan teselas. Una tesela incompleta no oculta ciudad válida.
4. **water_surface.mjs**: reconciliar la exigencia G19 de geometría costera OSM auténtica con los efectos mediterráneos ópticos del otro desarrollo. Una representación artística no debe generar una costa inventada. Conservar `prefers-reduced-motion` y material WebGL compilable.
5. **tests**: unir regresiones en vez de borrar tests de una rama; bloquear doble firma de fuentes, atravesar paredes y acceso a cualquier GLB privado.
6. **CI**: ejecutar `node --test tests/*.test.mjs`, `npm run build`, validación Chromium + escena y misión NPL/Conflictómetro. Solo después aceptar la rama integradora como candidata. Sin confundir el PASS de un módulo aislado con integración aprobada.

## Avance de este turno: trazabilidad anti-repetición

Se añade `tools/neurocity/cross_chat_lineage.py` (source-only) y cinco pruebas sintéticas con repos Git reales. El análisis lista los HEAD auténticos de las cuatro líneas, detecta rutas que cambian en más de una rama, verifica fuentes mínimas e impide incorporar archivos originales `.gml/.glb/.blend/.las/.laz` al contexto público.

El workflow horario existente `.github/workflows/neurocity-24h-convergence.yml` ahora cruza PR #46 y #41 sobre la rama apropiada, comprueba continuidad, archiva logs y **falla** si los merges temporales son incompatibles o no se ejecutan las pruebas. Esta mejora está en una rama independiente; no correrá en el cron de `main` hasta que se revise y fusione de forma explícita. La automatización de ChatGPT ya existente queda programada cada hora, pero no ejecuta trabajo permanente entre ciclos.

### Continuidad con Fábrica Huerto

La Fábrica Huerto es coordinación transversal y **no sustituye las bases originales ni la autoría de cada proyecto**. NeuroCity mantiene su propia línea G19/V50; NPL y Conflictómetro conservan la trazabilidad de indicadores agregados públicos. No usar pacientes, propietarios, datos individuales ni generar trabajadores identificables. El próximo paso material de alta prioridad es una resolución controlada de los siete conflictos de archivos (seis rutas únicas, repetida city_tiles), no abrir otra rama que implemente el mismo algoritmo de colisión o agua.

**Evidencia:** [GitHub Actions 39436363446](https://github.com/clucaina/NPL-CANONICAL/actions/runs/39436363446). La nueva revisión de este workflow debe revalidar los registros antes de declarar cualquier compatibilidad.
