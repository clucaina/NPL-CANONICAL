# NPL WORLD — demo autónoma sin red (10-10-2026)

## Iniciar el juego
**[Abrir HTML principal](https://raw.githack.com/clucaina/NPL-CANONICAL/main/demos/npl-world/index.html)**

Para evitar páginas intermedias de terceros o lentitud de carga, descarga el HTML desde GitHub y ábrelo localmente con Chrome o Edge. El juego **no** necesita red, CDN, API, MapLibre, WebGL ni Workers. El personaje se genera de forma volumétrica en el propio archivo.

- Teclas **WASD** caminar, **Mayús** correr, **V** cámara, **E** investigar, **M** mapa, **Espacio** saltar; arrastrar ratón para rotar, rueda para zoom.
- Entorno: recreación artística 3D por software (Canvas 2D), mosaicos, edificios, palmeras, vehículos, peatones y cinco misiones.
- Código sin archivos vinculados ni scripts remotos.
- Probado con Chromium/Playwright a través de set_content: sin excepciones; once controles funcionales verificadas. El entorno bloquea navegación a URL local o remota. Rendimiento de prueba aproximado 10–20 FPS según escena.

### Diferencias respecto al objetivo AAA
Esta demo **NO** contiene todavía una reconstrucción fotogramétrica exacta de Alicante, un avatar facial de Lucía ni animación PBR humana AAA. El archivo HTML evita el problema que impedía caminar, pero su calidad artística no reproduce la imagen de referencia.

### Historial de versiones
- [Versión geográfica v0.4 archivada](alicante_geografico_v04_archivado.html): dependía de MapLibre y modelos externos, con fallos de carga observados.
- [Versión de rescate anterior](alicante_rescate_3d.html): dependía de recursos y mapas externos.
- [Versión artística v0.2 archivada](escena_lowpoly_archivada.html): escena simplificada.
- [Prueba fotogramétrica Cesium/Google](alicante_fotogrametria.html): requiere clave y condiciones de Google, sin personaje.
