# Retail Media Lab: versión demostrativa

## Objetivo

Aplicación local interactiva, simulación causal y nueva política entrenada con
objetivo de conversión, restricciones explícitas y pruebas de reward hacking.
El usuario prohibió commit y push para este trabajo; todo permanece local.

## Arquitectura

Módulos nuevos lab_engine/lab_model/lab_training mantienen el experimento previo.
Servidor HTTP local con API de sesiones, pasos acotados y reportes de evaluación.
Frontend HTML/CSS/JS con fuentes y medios locales; sin compilación ni dependencias
web externas. Demo con reproducción/pausa, paso individual, escenarios, explicación
de candidatos, entrega por marca, métricas y comparación de resultados congelados.

## Trabajo y verificación

- [x] Motor causal y recompensa simétrica para orgánico/patrocinado, máximo una
  compra recompensada por sesión, sin incentivo monetario en reward.
- [x] Modelo de transiciones aprendido y planificación Bellman de horizonte finito,
  filtro empírico conservador, entrenamiento y evaluación
  con semillas disjuntas; baselines y escenarios de estrés.
- [x] API local validada, límites de recursos y tests HTTP sin dejar procesos.
- [x] Interfaz completa con estados de carga/error/vacío, navegación por teclado,
  responsive y movimiento reducido; controles verdaderos sobre el motor Python.
- [x] Auditoría Impeccable con evidencia renderizada y pruebas de interacción.
- [x] Revisión independiente del motor y de acabado, fixes verificados.
- [x] Documentación final del diseño: DESIGN.md y sidecar validados contra CSS.
- [x] Limpieza final de procesos de prueba: servidor local cerrado por SIGINT,
  sesión 43056 terminada con exit 0 y sin procesos de entrenamiento pendientes.

No se presume que un filtro conservador garantice no inferioridad ni que los
tests agoten todos los posibles ataques. Se reportarán fallos y límites reales.

## Evidencia de cierre

600,000 transiciones; partición 1700/2700/80020–80027. Siete políticas y cuatro
escenarios: 224 ejecuciones. Comparadores fuertes quality/greedy sin superioridad
estadística demostrada de RL. Escasez deja inversión pendiente explícita.

Dos hallazgos de revisión técnica corregidos: eventos que saltan de sesión al
abandonar y evaluación obsoleta tras reentrenar. Tests de regresión pasando.
Revisión visual independiente: arreglo único de eyebrow resuelto y verdict ship
para ese arreglo, luego documentación del sistema construido.
