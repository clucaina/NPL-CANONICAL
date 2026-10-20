# NeuroCity G19/V50 · V6 reparación localizada del mosaico de Explanada

**CANDIDATO PRIVADO · NO FUSIONADO · NO DESPLEGADO · NO FOTORREALISMO ACREDITADO**

## Cambio real

Se utilizó el GLB **original y sin modificar** `world-master/assets/selected/Explanada_v50_PBR_1024.glb` de la copia privada G19/V50. El generador:

1. Verifica su SHA-256 original y que incluye geometría triangular real, coordenadas UV y material PBR.
2. Detecta por cobertura real un rectángulo de 4×4 m dentro de la malla (X=318–322, Z=1378–1382, metros **locales** G19). **No son coordenadas ETRS89 absolutas ni una medición de campo**.
3. Recorta solamente 16 m² de los **9.215,9955 m²** de superficie proyectada del mosaico V50, conserva la malla restante y UV original y añade el mortero a la altura de la geometría original, sin solapamiento de polígonos de suelo.
4. Construye 10.000 piedras físicas de ~4 cm con cara superior y cuatro cantos (**100.000 triángulos de piedra**). Muestrea 40.000 esquinas en la malla V50 para ajustar altura y UV sin tangentes simuladas. Los tres subobjetos quedan unidos en un GLB glTF 2.0 propio.
5. Reutiliza el **material basecolor + normal map PBR original V50**, no recrea colores RGB que rompan la continuidad cromática. **No suplanta ninguna fachada, comercio, persona ni patrimonio**.
6. Prepara un **nuevo ZIP local reversible** de la ciudad conservando todos los archivos originales sin alterar y recuperando la versión previa del manifiesto. El manifiesto candidato usa el GLB de relieve solo en escritorio y declara el GLB V50 original como fallback en móvil. La selección de ese fallback necesita el código de la rama de revisión: el `game.js` del ZIP heredado **todavía no se recompiló con ella**. No aprobar uso móvil hasta ese paso.

## Verificaciones y límites

- Geometría original proyectada = 9.215,9955 m²; recorte = **16,0000 m²**; error de conservación inferior a la precisión de auditoría (calculado en 64 bits).
- 5 controles unitarios Python, de ellos 4 sobre datos sintéticos y 1 sobre fuente V50 privada cuando está disponible. Las pruebas sintéticas no contienen activos privados.
- Renderizamos ambos GLB con **VTK CPU** con el mismo objetivo y cámara para contrastar el aspecto. En 400 puntos, clasificación de color coincide **99%**; error medio RGB **4,2/255**. Esto comprueba consistencia del render de fuente y candidato **bajo esa cámara y entorno**, NO fotogrametría ni validez en WebGL.
- Se detectó y corrigió una regresión real: el primer candidato reconstruía incorrectamente la fase de color a partir de píxeles y producía un cuadrado artificial evidente. Se sustituyó por interpolación UV y material original.
- Browser original desde localhost bloqueado por `ERR_BLOCKED_BY_ADMINISTRATOR` en este entorno. No se ha medido FPS ni jugabilidad con el nuevo GLB, ni triangulación física/collisiones en una partida G19 real.
- Elevaciones y superficies originales G05/G13 no son topografía oficial; no debe sustituirse la física del personaje ni usarse en proyectos clínicos.
- El único fichero de producción modificado en el ZIP candidato es **una copia del manifiesto local**, que apunta a un archivo adicional, nunca sobrescrito sobre el original. Ninguna publicación o transmisión a terceros.

## Reproducción únicamente en local

Requiere **la copia propia** `NEUROCITY_ALICANTE_G19_FISICA_COSTA_MAR_V5_LOCAL.zip` y los fuentes abiertos `build_mosaic.py`, `v50_surgical_tessera.py`, `install_local_candidate.py`.

```sh
python -m pip install numpy scipy pillow trimesh
python v50_surgical_tessera.py --archive /ruta/al/V5.zip --builder build_mosaic.py --out Explanada_V50_Surgical_4cm_STONES_PRIVATE.glb
python install_local_candidate.py --base-zip /ruta/al/V5.zip --model Explanada_V50_Surgical_4cm_STONES_PRIVATE.glb --audit V50_SURGICAL_PATCH_AUDIT.json --out-zip NEUROCITY_G19_V50_V6_CANDIDATA.zip
python -m unittest discover -s . -p 'test_v50_surgery.py' -v
```

La prueba científica/fotográfica pendiente es emparejar un punto real con la geometría fuente; esta corrección conserva fielmente un **modelo histórico**, no demuestra que ese modelo replique milimétricamente Alicante. La prueba técnica pendiente es compilar el último visor integrador de las PR paralelas (#29 mar, #30 física, #31 teselas y #32 Catastro) y abrirlo en un navegador con los modelos locales y FPS/RAM medidos; **no fusionar ramas a ciegas**.