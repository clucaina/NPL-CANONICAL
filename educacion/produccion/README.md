# Producción audiovisual educativa

Este directorio conecta los laboratorios de Neuropsicolucía con un **guion de producción que se puede reutilizar en VideoForge** cuando dispongamos de su adaptador o de un motor de render válido.

Contiene dos piezas originales, de aproximadamente 70 segundos cada una, y seis planos totalmente escritos por pieza. Se conservan duración, intención visual, narración, subtítulo y fuentes. Los ejemplos son ficticios.

## Exportar los materiales aprovechables hoy

```bash
python3 educacion/produccion/exportar_guiones.py \
  --input educacion/produccion/guiones-audiovisuales.json \
  --output /tmp/formaciones
```

El script, sin dependencias de terceros, genera para cada pieza:
- `.srt`: subtítulos con tiempos exactos según el guion, no sincronía de voz real;
- `.csv`: lista de planos y narraciones lista para importar a un editor;
- `.md`: guion técnico legible y verificable.

Para comprobar los datos **sin generar archivos**, añade `--dry-run`.

## Alcance

Los MP4, el sonido, el doblaje y cualquier presentador humanoide **no se generan en este módulo**. No se asegura que el formato sea importable directamente por VideoForge dev120; se requiere un adaptador específico que respete su esquema interno. VideoForge dev120 todavía tenía pendiente validar inferencia generativa real con GPU.

Los subtítulos son estimaciones del montaje y necesitarán resincronización tras grabar o generar el audio. No se permite utilizar la imagen o la voz de una persona sin los derechos/consentimientos aplicables.

## Validación

```bash
python3 -m unittest discover -s educacion/tests -p 'test_storyboard_export.py'
```

No editar aquí los proyectos activos de NeuroCity, VideoForge ni Psicología Política. Esta carpeta es una librería audiovisual de Neuropsicolucía.
