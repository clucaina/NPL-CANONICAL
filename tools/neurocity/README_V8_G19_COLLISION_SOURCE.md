# NeuroCity V8 · G19/V50 / NPL / Casa Carbonell G14 / barrido continuo

Material propietario: solo en ZIP privado de Lucía. Esta rama **NO** contiene ningún GLB, copia de clientes, imagen privada ni dato pericial.

Código consolidado aquí: PR #46 (G19 wall sweep) sobre PR #45 (G14 Carbonell), junto al ensamblador validado de PR #44. **Las PR no se han fusionado en producción.**

Fuente compilada: GitHub Actions `39430608426`, head `093b94856eced23ec640b629780bd55d67ebb631`, artefacto `12267194249` (solo game.js+index.html), sha256 ZIP `2f746acbf4d2ef1b1342b1fe5722c582d899f452ae90f27ea7fe6257cd06bc8a`, sha256 `game.js` `722b6b0bde72cfc347a5b101c5d6fac86db25f647b6ca3bedd7ec823f79b905d`.

Paquete G19/V50 V7 owner-only SHA256 `8abd0c0ea2601d913a4c52618101a6712af85228133b61dd34759f0749836403`. Resultado V8 owner-only SHA256 `bda1d7738c4fc1d5929f553570166be3b2286bcc10feb19a330df995258c4b31`, 62.653.432 bytes, 86 GLB preservados y 88 referencias con hash y tamaño comprobados. Se preserva `INTEGRACION_WEBGL_V7_REVISABLE.json` y añade `INTEGRACION_WEBGL_V8_G19_SWEEP_REVISABLE.json` sin sobreescritura. Cuatro lanzadores confinados a 127.0.0.1. 10 tests sintéticos locales de seguridad y reproducibilidad satisfactorios.

Limitaciones: código de barrido continuo probado, pero **falta WebGL con GLB privados + recorrido longitudinal real + colisiones a distintas cotas + FPS y topografía validada**. El navegador CI público no certifica esas pruebas. No usar para release ni redistribución.
