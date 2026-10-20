# NeuroCity V7 · fuente de verdad recuperada de otros chats
**2026-10-20 · rama independiente · DRAFT · no desplegar / fusionar / publicar binarios privados**

## El bloqueo real era una REGRESIÓN, no ausencia de diseños
**NPL:** la UI de NeuroCity PR #33 utilizaba `npl_brain3d.mjs`, dos hemisferios esféricos falsos, cinco pulsos dibujados y una interpretación de juego. Esta NO es la anatomía ya construida en NPL. El archivo NPL original existe en la **biblioteca privada de la usuaria**, archivo `NPL-CANONICAL-C14-R3-NEUROVISUAL-SYSTEMS-OS.zip`. Se recuperó y verificó:
- `public/assets/brain/brain.glb` (4.650.816 bytes, SHA256 `76a49ea4526a4880613aec7a02756bd7301b0b9d0680d7cae33e197b672c5453`), 437 nodos GLTF, 437 mallas, **563 primitivas Draco**.
- `public/assets/brain/manifest.json` (137.895 bytes, SHA256 `36385df49ce862455b864c7ea25e405badab2bd4953a949a2fa4240b1ff549ad`), 437 identificadores anatómicos con `gltfNodeIndex` explícito. **437 estructuras ≠ 563 primitivas**, no imponer relación 1:1.
- `src/components/BrainViewer.tsx` (9.160 bytes, SHA256 `bc9f607da0dbc9a321dce9ed2df74d3ffc4670a1c07558951d84e493092a46d8`), **sin cambiar un byte**.
- Three.js 0.167.1, Draco r167 LOCAL, React 18.2.0. El paquete de dependencias fue compilado mediante GitHub Actions SIN publicar ningún GLB de la usuaria: https://github.com/clucaina/NPL-CANONICAL/actions/runs/39420312619
- Proveniencia upstream original Z-Anatomy/BodyParts3D, CC BY-SA 4.0 según `provenance.json`; cumplir atribución y revisión de licencia antes de distribución.

El código publicable `canonical_npl_contract.mjs` solo **exige el manifiesto y GLB exactos por SHA256 antes de abrir en iframe el React BrainViewer ORIGINAL**, y rechaza un cerebro procedural como fallback. `app.js` no importa ni ejecuta `npl_brain3d.mjs`. El comportamiento de juego se conserva en `NPL_GAME_BEHAVIOR`, sin afirmar medición cerebral, y las herramientas NPL/Conflictómetro están disponibles como misión secundaria.

### Geografía y mosaico: fuente original, no reinterpretación 4px
El archivo **privado** `NEUROCITY_G19_V50_V6_EXPLANADA_INTEGRADA_PRIVADA_CANDIDATA.zip` contiene los modelos anteriores de Alicante y una mejora posterior que NeuroCity PR #33 había omitido:
- `world-master/assets/selected/Explanada_V50_Surgical_4cm_STONES_PRIVATE.glb`: 11.176.704 bytes, SHA256 `6a7be6245c7680ea73154a6e90d448af27e3b5abd0859f8ef96368e495601636`. ~10.000 piedras 3D físicas de 4 cm sobre **16 m²** del mosaico histórico V50 con color y normal PBR **originales**. Un modelo de pruebas, **no es reconstrucción milimétrica validada en terreno**.
- Escritorio: cargar este GLB; móvil: fallback real del propio archivo histórico V50 `Explanada_v50_PBR_1024.glb`, ~5.225 triángulos, **no sobreponer ambos**. Las pruebas de selección están en `tests/recovered_master_tiles.test.mjs`.
- El GLB histórico de la ciudad G19/V50 conserva geometría original, 12 rejillas físicas G13 y los materiales del propietario. Puerto, árboles OSM y textura PNOA pública son una base cartográfica distinta. No confundir calidad geométrica ni proveniencia de una con la otra.

### Local privado V7 (NO subir a GitHub)
Constructor reproducible: `tools/neurocity/private_local_v7_build_reference.py` (si está disponible, usa entradas verificadas y nunca publica las fuentes). La entrega local conserva las **77 entradas GLB** del manifiesto histórico (incluido candidato quirúrgico), las 12 cuadrículas de fuente G13 y datos revisados originales de Conflictómetro. El visor NPL original se empaqueta sin cambiar los tres hashes protegidos. Si no existen las fuentes privadas, **fallar**: nunca reconstruir anatomía falsa ni inventar GLB.

### QA y límites
- Fuente y bundle abiertos verificados en CI (Node, Python, Chromium público SIN GLB privado), ver https://github.com/clucaina/NPL-CANONICAL/actions/runs/39421141962.
- El GLB 437/563, la integridad SHA, y la compilación de `BrainViewer.tsx` sí se verificaron contra bytes reales **locales**.
- **La renderización privada de los 437 atlas anatómicos en un Chromium real dentro del ZIP no está acreditada.** Navegación localhost bloqueada por `ERR_BLOCKED_BY_ADMINISTRATOR` en el entorno. Requiere prueba real en Windows. Análogo para los 77 modelos históricos de Alicante juntos. **NO atribuir FPS, controles, ni fotorrealismo certificados**.
- Prohibido incluir pacientes, trabajadores reales, avatares biométricos o material fotográfico privado en pruebas públicas. Este repositorio público contiene **contratos y pruebas sin los binarios protegidos**, nunca sube el ZIP local.
- Mantener esta distinción **en todas las ramas y chats**: `NPL` posee original `BrainViewer`; `NeuroCity` es consumidor, no propietario de una anatomía alternativa. Si falta archivo, mostrar error fiable, sin fallback ficticio.

## Próxima auditoría de continuidad
Toda nueva versión debe verificar: hash atlas + manifest + visor, 437/563, fuente React/Three/Draco, manifest G19 77 GLB, fallback V50 móvil, geometría física del mosaico, física G13 12, contratos NPL/Conflictómetro, y mantener la ciudad pública operativa cuando faltan binarios privados. Evitar contar líneas/capturas como sustituto de ejecutar modelos reales.
