# Seis voces, ¿cuántas fuentes?

Laboratorio interactivo original para alfabetización en memoria y testimonio. **Destino:** Neuropsicolucía, sección Recursos o Aprende. Puede reutilizarse en la formación de SICNAR mediante una integración independiente, tras revisión metodológica.

## Qué hace
- Presenta seis declaraciones enteramente ficticias con horas, contenido y dudas contrastables.
- Permite elegir una persona, leer su declaración y cambiar en el ejercicio la ruta declarada de su información.
- Muestra un grafo SVG con enlaces, identifica dependencia declarada y detecta atribuciones circulares.
- No fusiona personas con origen desconocido en una falsa fuente única.
- Exporta las rutas en CSV saneado y un cuaderno con notas en JSON, sin comunicar nada a un servidor.
- Diferencia visualmente observación propia **declarada** de corroboración independiente **demostrada**.

## Restricción científica
El programa no puntúa credibilidad, no diagnostica memoria ni identifica falsedad. Una ruta declarada puede tener información compartida no reconocida, y dos observaciones directas pueden no ser independientes. El grafo es una herramienta de enseñanza metodológica, **no un resultado pericial**.

## Fundamentación
- Kękuś y colaboradores (2024), *Online misinformation can distort witnesses' memories. Analysis of co-witness discussions using an online version of the MORI-v technique*. https://pubmed.ncbi.nlm.nih.gov/38298368/
- Mori y Kishikawa (2014), *Co-witness auditory memory conformity following discussion*. https://pubmed.ncbi.nlm.nih.gov/24897885/
Los estudios documentan posibles efectos de discusión entre testigos en entornos experimentales, no una regla universal aplicable a toda declaración.

## Integración
La ruta `educacion/fuentes-dependientes/index.html` es autónoma, no requiere API ni datos de usuarios. Montar en Recursos de Neuropsicolucía y enlazar desde materiales SICNAR si se aprueba. Para trabajar con casos reales, **no utilizar esta edición**; sería necesario un sistema profesional de fuentes autenticadas, permisos, seguridad y validación.

## Comprobación
`node --test educacion/fuentes-dependientes/tests/test-provenance.mjs`.
La prueba automatizada verifica rutas dependientes, orígenes no identificados, ciclos, sintaxis y ausencia de telemetría. La prueba manual en navegador y la revisión científica son pasos distintos.
