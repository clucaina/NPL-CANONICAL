# Fábrica independiente: NPL-CANONICAL

Esta automatización solo afecta a **clucaina/NPL-CANONICAL**. No crea una app común ni transfiere información entre proyectos.

## Reglas
- Trabajar exclusivamente en ramas de desarrollo y mediante revisión. No fusionar, desplegar, publicar ni cambiar infraestructuras automáticamente.
- El informe de auditoría muestra archivos visibles, bloqueos y acciones propuestas; **no ejecuta las pruebas funcionales de la aplicación**.
- No incluir datos personales, clínicas, informes periciales, credenciales ni secretos.
- No habilitar llamadas a IA de pago ni usar servicios externos para datos sensibles.
- No crear versiones paralelas ni reconstrucciones del cerebro; resultados simulados no equivalen a diagnosticos.

## Cola de ejecución propia
1. Sincronizar codigo completo en fuentes individuales antes de continuar.
2. Verificar Brain Gate y Brain Runtime con ejecucion real de pruebas.
3. Explorar experiencias NeuroCity con simulacion util y modo 2D accesible.
4. Auditar rendimiento, geometria, dispositivos moviles y navegacion por teclado.

## Qué hace y qué no hace
El script y el workflow de GitHub solamente realizan una **auditoría de solo lectura**. La ejecución periódica del workflow no estará activa hasta incorporarlo deliberadamente a la rama predeterminada; por eso esta propuesta se entrega en una rama y PR de borrador. No implementa una IA que programe sola ni equivale a despliegues continuos. GitHub Actions en repositorios privados está sujeto a una cuota de ejecución.
