# NPL WORLD · Alicante fotogramétrico / avatar humano GLB

**Abrir proyecto fuente:** [Visualización de Alicante](https://raw.githack.com/clucaina/NPL-CANONICAL/main/demos/npl-world/fotorrealismo/index.html)

## Diferencia fundamental con prototipos anteriores
Este HTML no fabrica calles, palmeras ni edificios. Solo visualiza mallas geográficas 3D reales con sus texturas suministradas por **Google Photorealistic 3D Tiles** a través de CesiumJS. No presenta una recreación procedimental como si fuese Alicante.

Se centra en la Explanada de España de Alicante: longitud **-0.48322**, latitud **38.34402**. Añade miradores del puerto y castillo, y un importador de personaje 3D **GLB local** cuya escala es de 1 metro por unidad de mundo.

## Requisitos para ver un resultado visual real

1. Proyecto en Google Cloud con **Map Tiles API habilitada**, facturación y una **clave válida**. Introduce la clave al arrancar (no se guarda ni se publica). Limita la cuota de facturación para evitar sorpresas. Deben respetarse los términos del producto y los derechos de atribución. [Google API oficial](https://developers.google.com/maps/documentation/tile/3d-tiles).
2. Conexión a Internet para CesiumJS y los 3D Tiles.
3. Para mostrar una persona realista: descarga un **GLB humano completo** o carga un GLB personalizado. El modelo genérico femenino [Riley CC0](https://www.innerscene.com/tools/library/3d-parts/riley-3d-person-woman-standing-8d40398f) no reproduce a Lucía. El botón que intenta descargarlo automáticamente puede fallar si el origen tiene CORS; en ese caso, descárgalo y selecciónalo mediante archivo local.
4. **Para la identidad de Lucía:** se necesita un modelo de cuerpo y rostro construido con referencias reales y licencia/consentimiento; actualmente no está creado ni validado. No hay MetaHuman ni reconstrucción facial oculta en este repositorio.

### Cómo arrancar en Windows
Descarga el ZIP [del chat] con este directorio, descomprime y ejecuta **INICIAR_WINDOWS.bat** (requiere Python); visita `http://127.0.0.1:8000`. El navegador descarga CesiumJS y los mosaicos Google cuando introduce la clave. Es un visor de calidad fotogramétrica condicionado a los servicios externos; no es un juego offline.

### Validación realizada
Sintaxis JavaScript comprobada con Node 22. Pruebas de interfaz en Chromium: sin credenciales la página explica qué falta; con CDN bloqueado el aviso aparece y no simula un mundo 3D falso. **No ha sido posible validar un render fotorrealista efectivo sin una clave Google proporcionada por el propietario del proyecto**.

### Qué falta para un MVP comparable visualmente con un videojuego comercial
- Un GLB humano PBR de la propia Lucía (cara reconocible, pelo y ropa detallados), con rig y evaluación visual.
- Validar cobertura/resolución de fotogrametría específicamente sobre la Explanada y el puerto; el servicio no garantiza en todos los sitios el mismo nivel de detalle.
- Alinear el modelo con la superficie, solucionar colisiones, sombreado, contactos y cámaras a nivel de calle.
- Un motor GPU de juego (por ejemplo Unreal Engine 5 + Cesium for Unreal) y una cadena de animación profesional; el visor web actual prioriza inspección visual.
