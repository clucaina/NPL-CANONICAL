# NeuroCity G19/V7: barrido continuo

Base: PR #45, SHA da17a5b0f86be7d492131949cab860007c658854.
Parche: PR #46, SHA a31b5c235d745f3a616845e56281bddbed8d6626.
Defecto: una pared real en z=0 podia atravesarse desde z=-0.45 hasta z=+0.55 en un solo paso.
Archivos: visual_viewer/collision_sweep.mjs, city_collision.mjs, tests/collision_sweep.test.mjs.
Node local: 6/6 PASS; no demuestra WebGL. CI final y datos G13 pendientes.
No hay datum LiDAR certificado, ni FPS, ni fachadas fotorrealistas. No tocar GLB privado, NPL, Conflictometro, Fábrica Huerto; sin fusion ni despliegue.
