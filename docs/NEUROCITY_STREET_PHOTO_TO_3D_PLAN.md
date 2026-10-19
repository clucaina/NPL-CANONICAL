# NeuroCity · de fotografía callejera licenciada a ciudad 3D verificable
Fecha: 19/10/2026. Etapa: prototipo aislado en rama PR #20; **NO producción**.

## Auditoría del problema visible (con evidencia)
El visor original tenía fachadas OSM extruidas sin material fotográfico, setos de geometría simple y un asfalto gris plano. Los planos artísticos superpuestos hacían que la ciudad pareciera una maqueta aun cargando PNOA. Se han aplicado UV mundiales y materiales de asfalto originales sobre las **cintas de carreteras cartografiadas en OSM**; los setos nuevos son ilustrativos y no árboles geolocalizados. No afirmar fotogrametría hasta reconstruir desde imágenes.

## Descubrimiento real (consulta de metadatos reproducible)
Sector geográfico: WGS84 bbox `-0.4862,38.3418,-0.4795,38.3470`.
- Instancia Panoramax IGN `https://panoramax.ign.fr/api/search`: **0** registros devueltos en área.
- Federación Panoramax `https://api.panoramax.xyz/api/search`: **100** imágenes en primera página y **3** secuencias. La más larga tiene **95** imágenes visibles en esa página (puede haber más).
- **99/100** tienen enlace individual `https://creativecommons.org/licenses/by-sa/4.0/`; **1** sin atribución aceptable en resultado, EXCLUIDA.
- Inventario y auditoría de los derechos se guardan en un artefacto de CI sin imágenes JPEG y sin información de contribuidores.
- KartaView `https://api.openstreetcam.org/2.0/photo/`: respuesta distinta del esquema esperado, registrada como bloqueo; no puede inferirse ausencia de cobertura.
- Ninguna de estas cifras indica que exista reconstrucción densa viable. Falta comprobar fecha, calibración, solapamiento, objetos móviles y control de errores contra ortofoto/LiDAR.

## Motor abierto ya preparado
Pipeline experimental `tools/neurocity/photogrammetry_probe.py` en GitHub Actions: escoge SOLO fotos con enlace de licencia individual confirmado, preserva el grupo de secuencia, rechaza URLs inseguras, admite máximo 20 fotografías públicas JPEG hasta 6 MiB por imagen y genera copias de trabajo comprimidas, sin EXIF, en directorio temporal. Usa **COLMAP**, herramienta SfM/MVS abierta (licencia BSD), primero para extraer y comparar características y luego triangulación dispersa.

La prueba reporta número de imágenes que COLMAP registra y puntos 3D triangulados. El artefacto de GitHub contiene SOLAMENTE estadísticas y razones de bloqueo, NO imágenes, ni cámaras con rostros, ni modelos derivados, y borra los temporales al finalizar. Si falla por restricciones de foto URL, registro de cámara, licencia o datos, **no** se declara éxito.

## Qué constituye un modelo 3D real usable de Alicante
1. **Fuente legal**: fotografías de secuencia CC BY-SA individualmente verificadas; privacidad y caras/matrículas anonimizadas. No Google Street View: sus términos restringen construir modelos geográficos derivados.
2. **Reconstrucción efectiva**: >=5 cámaras registradas por COLMAP, >=100 puntos triangulados, error de reproyección inspeccionado. Ni esto equivale a fachadas densas o texturas fotorrealistas.
3. **Reconstrucción densa y textura**: cámaras útiles con diversidad de puntos de vista, máscaras de cielo/vehículos/personas; PatchMatch/fusión, malla watertight parcial y atlas UV. Descartar duplicados con huecos enormes.
4. **Georreferenciación**: ajuste robusto a OSM (planta) y LiDAR 3ª cobertura PNOA para altura. Nunca deformar la geometría medida para ajustarse a fotos sin comparar residuales. Guardar RMSE y errores.
5. **Optimización GPU**: mallas GLB por tramos, instancias, texturas KTX2/Basis, LOD, culling y presupuesto de memoria. Revisión de hardware móvil y desktop, p50/p95 FPS real.
6. **Licencias separadas**: CC BY-SA derivados fotográficos en capa propia con atribución y condiciones share-alike; ODbL para datos OSM; PNOA/IGN con atribución oficial; los algoritmos COLMAP/Blender no cambian derechos de imágenes.
7. **NPL y Conflictómetro**: contratos versionados como capas funcionales independientes, únicamente indicadores agregados de fuentes públicas verificadas; originales intactos.

## Recursos concretos
- Federación fotográfica Panoramax STAC https://api.panoramax.xyz/api/
- KartaView CC BY-SA 4.0 https://kartaview.org/terms y API https://kartaview.org/doc/photos
- COLMAP SfM/MVS https://colmap.github.io/ (software BSD)
- LiDAR PNOA 3ª cobertura https://pnoa.ign.es/web/portal/pnoa-lidar/productos-a-descarga
- Condiciones Google Maps Platform https://cloud.google.com/maps-platform/terms
- Licencia CC BY-SA 4.0 https://creativecommons.org/licenses/by-sa/4.0/deed.es

No se han exportado fotografías privadas ni realizado gastos, publicaciones o fusiones.
