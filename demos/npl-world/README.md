# NPL WORLD — objetivo visual premium

**[Nueva ruta: Alicante fotorrealista 3D y avatar GLB real](fotorrealismo/index.html)**

El archivo en `fotorrealismo/index.html` carga fotogrametría real de Google Maps mediante Cesium; requiere clave de Map Tiles API con facturación habilitada. **Sin credenciales no inventa edificios, no muestra un falso GTA y explica qué acceso falta.** Permite importar un humano real .glb local sin transmitir el archivo y ofrece un modelo CC0 de muestra (no representa a Lucía). [Requisitos y verificación](fotorrealismo/README.md).

La reconstrucción facial personalizada de Lucía y la prueba real de la cobertura de Google en Alicante están pendientes. Este es un **integrador visual técnico**, NO una demo GTA terminada.

---

## Historial de prototipos previos


## Nueva escena 3D editable — prioridad visual

[**Abrir NPL WORLD Alicante en el visor 3D**](https://higgsfield.ai/3d-jutsu/5673fb30-1e3c-4166-9904-b8744139eb1b)

Se ha creado una **escena volumétrica en Blender**, exportada a GLB (12,8 MB) y BLEND (16,1 MB). [Ver auditoría de los activos y límites](ESCENA_3D_HQ.md).

**Importante:** la escena es una reinterpretación artística, no es una réplica GTA/fotogramétrica validada. El avatar aún no reproduce los rasgos de Lucía ni está riggeado. La visualización requiere conexión a Higgsfield.

---

## Demostración jugable antigua (legado)


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
