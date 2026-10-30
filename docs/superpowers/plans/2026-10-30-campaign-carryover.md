# Campañas con saldo continuo

Objetivo: conservar saldo y atraso de cada marca entre días, usando el modelo
entrenado existente y sin alterar su tabla Q ni los resultados diarios originales.
Trabajo en main por solicitud del usuario; autoría gar22210@uvg.edu.gt.

El límite del día será la meta acumulada exacta menos lo ya gastado:
`budget_cents * (day + 1) // campaign_days - cumulative_spend_cents`.
Así se recuperan días de tráfico bajo y el redondeo llega al presupuesto completo
el último día. Nunca se cobran impresiones ni se inventan clics para consumir saldo.

- [x] Tests de arrastre, redondeo, sobregiro, cierre inválido y días sin tráfico.
- [x] Ledger secuencial, asignación opcional en el entorno y runner de campaña.
- [x] Comando campaign, tráfico configurable y reportes JSON/CSV por marca/día.
- [x] Ejecutar campaña sintética y suite completa; revisión independiente sin hallazgos.

La campaña es una trayectoria continua, no 30 réplicas independientes: su CVR
se pondera por sesiones y no se calcula un IC tratando sus días como independientes.
El reporte marca inversión pendiente y metas incumplidas. No se garantiza gasto
total si el CPC indivisible, el tráfico o los clics impiden entregar todo.

Resultado del escenario incluido: 31,200 sesiones; gasto USD 7,999.60 de 8,000;
residuo USD 0.40 menor al CPC de Nova. Sin sobregiros. CVR 10.6987% frente a
10.5929% orgánico emparejado. La tabla Q original permanece intacta.

Verificación: 26 tests pasan; nueve son nuevos de campaña. El reviewer
`/root/review_mvp` ejecutó la suite y no encontró errores accionables.
