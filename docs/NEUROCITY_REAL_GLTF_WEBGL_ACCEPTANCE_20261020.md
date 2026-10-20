# NeuroCity Alicante · 3D oficial realmente cargado en Chromium

Estado: desarrollo experimental independiente. **NO fusionar, publicar ni desplegar**. No existen promesas de ejecución 24 horas desde este archivo.

## Salto verificado: Blender → visor → WebGL → lección NPL

- PR #37: https://github.com/clucaina/NPL-CANONICAL/pull/37
- CI real: https://github.com/clucaina/NPL-CANONICAL/actions/runs/39419406395
- Commit probado: e31fd95494e207f111d9f7c2c5621436eb4ed151
- Blender reconstruyó Alicante real desde **8/9** sectores oficiales del Catastro (r0_c1 tuvo fallo de conexión). El 9/9 se había demostrado separadamente en 39414183545.
- Modelo: **614 edificios de base OSM**, 38 con sección oficial emparejada, **155 secciones reconstruidas** y **52 partes oficiales adicionales** sin colisión OSM; son **207 partes**, no 207 edificios completos ni fachadas fotográficas.
- GLB real de 1.277.900 bytes, SHA-256 7735640b2e797aef8f5273559fe4dd2dd427882ca747555ee96d0e71f128e9d3.
- Chromium/SwiftShader local cargó exactamente ese GLB tras verificar hash, confirmó **6 mallas / 21.376 triángulos**, mar mediterráneo procedimental, alternancia gráfica y finalización de la misión educativa NPL/Conflictómetro (datos públicos de demostración, no base completa).
- Informe marcado `private_webgl_qa: PASS`, `private_webgl_npl_mission: true`.
- Geometría fuente GML y GLB privado guardados solo en directorio efímero de la ejecución; capturas privadas no se subieron. Se publicaron exclusivamente metadatos agregados y resultados de software.

## Siguiente bloqueo físico

El visor permite caminar atravesando las paredes del GLB. PR #39 agrega colisiones exactas derivadas de los triángulos verticales de sus muros, un índice de celdas de 12 metros y un radio de desplazamiento de 0,58m, con deslizamiento junto al muro. La ejecución integral propia de PR #39 debe terminar en éxito **antes** de afirmar que estas colisiones funcionan sobre Alicante oficial. Los obstáculos no están inventados: se derivan del modelo auténtico ya cargado.

## Límites insalvados

- `plantas catastrales × 3m` constituye altura ESTIMADA, no medida por LiDAR.
- Fachadas y rótulos no son fotogrametría ni inventario exacto de locales. Interiores y trabajadores reales no están modelados.
- Un test con SwiftShader certifica funcionamiento de WebGL, pero no FPS, VRAM, batería, fluidez en smartphones reales ni MMO.
- Georreferenciación horizontal no significa precisión milimétrica vertical.
- NPL y Conflictómetro: se comprueba el **contrato público y la misión educativa**; los originales completos no han sido importados ni modificados. No se admiten datos personales o de pacientes.

## Próximas puertas de calidad

1. Realizar la prueba Chromium completa de las colisiones en PR #39, con contadores positivos de segmentos y celdas.
2. Medir alturas por LiDAR-PNOA de cubiertas y terreno, con datum/fecha/residuales contrastados.
3. Probar captura visual real, FPS y memoria GPU en hardware móvil.
4. En otra rama y con derechos de redistribución resueltos, producir una versión descargable para el usuario, sin fuentes GML originales, datos privados ni publicación automática.
5. Planificar la geometría por nivel de detalle y teselas locales para ampliar a toda España, sin cargarla a la vez.
