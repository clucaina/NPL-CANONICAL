# Laboratorio de inferencia y tasas base

Módulo original de NPL, preparado para integrarse en la sección educativa de **Neuropsicolucía**. No sustituye al atlas anatómico ni a la evaluación neuropsicológica.

## Funcionalidad real
- Manipulación de prevalencia, sensibilidad, especificidad y tamaño de población de 100 a 1.000 personas ficticias.
- Representación pictográfica de resultados, matriz TP/FP/FN/TN y VPP/VPN.
- Ejercicio de estimación para comparar intuición y cálculo.
- Exportación CSV, JSON e impresión a PDF a petición de quien lo use.
- Cuatro perfiles de configuración, sin datos de pacientes, sin telemetría y sin cookies.
- HTML autónomo. Los parámetros iniciales son **simulados**, no datos clínicos publicados.

## Implantación
Copia `educacion/inferencia-tasa-base/index.html` a una ruta de Recursos o Aprende en la web de Neuropsicolucía. Conecta el enlace en la navegación, revisa su diseño con el sitio y comprueba acceso por teclado, lectura de pantalla y funcionamiento en móvil. No incrustes un formulario de Google Analytics que capture la respuesta ni los parámetros del ejercicio.

## Modelo
En cohorte n, con prevalencia p, sensibilidad s y especificidad e, calcula:
- casos con condición D = round(n*p);
- verdaderos positivos TP = round(D*s);
- falsos negativos FN = D-TP;
- falsos positivos FP = round((n-D)*(1-e));
- verdaderos negativos TN = n-D-FP;
- VPP = TP/(TP+FP) si existe un positivo.

Los parámetros se introducen en porcentaje. La representación usa personas enteras redondeadas, por tanto puede diferir marginalmente de cálculos sobre probabilidades continuas. La representación no valida ninguna prueba real.

## Fuente científica
- BMJ, *Interpreting diagnostic accuracy studies for patient care* (2012): https://www.bmj.com/content/345/bmj.e3999.

## Puerta de calidad
Ejecutar `node --test educacion/inferencia-tasa-base/tests/test-base-rate.mjs`.
Después verificar manualmente teclado, pantalla pequeña y exportaciones en el navegador; no se consideran completadas automáticamente por los tests de código.
No publicar en la web real sin revisión de contenido y accesibilidad.
