# NPL WORLD — Alicante · MVP técnico (10/10/2026)

## Demos
- [Escena 3D navegable](https://raw.githack.com/clucaina/NPL-CANONICAL/main/demos/npl-world/index.html): **WASD**, ratón, Mayús, E, V, P; Explanada, edificios mediterráneos y Marina reinterpretados artísticamente. No es cartografía exacta.
- [Alicante 3D fotogramétrica](https://raw.githack.com/clucaina/NPL-CANONICAL/main/demos/npl-world/alicante_fotogrametria.html): Google Photorealistic 3D Tiles con Cesium, requiere clave Map Tiles API, conexión, condiciones y posible facturación.

La pasarela raw.githack muestra un aviso de seguridad al abrir por primera vez HTML alojado en un repositorio de terceros.

## Modelo humano
El prototipo carga un [humano animado CC0 de Innerscene](https://www.innerscene.com/tools/library/3d-parts/locomotion-collection-harper-3d-person-animated-797e1e2a); puede fallar por permisos CORS y el archivo GLB también se puede importar desde el botón **AVATAR GLB**. Es un modelo de muestra; **no reproduce la cara de Lucía**.

## Estado verificado
Código publicado en GitHub; ambos scripts pasan verificación sintáctica con Node 22; comprobación estática del DOM y referencias internas. **No hay verificación automatizada end-to-end de renderizado/animación con los GLB externos** ni integración efectiva de indicadores NPL. No debe presentarse como AAA/fotorrealismo integral terminado.

## Próximo hito de producción
Modelado de personaje propio desde referencias visuales autorizadas, texturas PBR y rig locomotor; datos urbanos georreferenciados con calidad demostrable; colisiones y grounding de pies sobre terreno; pruebas reales de FPS y navegación en navegador y dispositivo.
