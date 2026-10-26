# Retail media con aprendizaje por refuerzo

MVP para una entrega parcial: un agente **Q-learning ya entrenado** elige qué
producto patrocinado mostrar en un grid de retail media. Busca conservar el CVR
de la web y entregar inversión a cada marca mediante cobro **CPC** y pacing.
Todo el tráfico, catálogo, marcas y comportamiento son sintéticos.

**Demo lista para abrir:** [reports/demo.html](reports/demo.html). Descarga el
repositorio y abre ese archivo en tu navegador: funciona sin servidor, internet
ni instalación de Python. GitHub muestra el código del HTML, no ejecuta la demo.

## Qué incluye

- Bloques de **20 productos**; únicamente los spots **3, 4, 5, 6, 11, 12, 13 y 14**
  admiten patrocinados. La numeración es desde 1 y se repite por bloque.
- Tres intenciones/categorías, tres marcas y 18 productos patrocinados.
- Acción de conservar el orgánico o elegir un producto patrocinado.
- Presupuestos monetarios en centavos, cobro solo por clic, prevención de
  sobregiros y de patrocinados duplicados en un mismo bloque.
- Pacing que limita adelantos y exige oportunidades para marcas atrasadas.
- Modelo guardado, curvas de entrenamiento, cinco políticas de comparación,
  exportaciones CSV/JSON y una demo que reproduce decisiones del modelo.
- 17 pruebas automatizadas sin dependencias adicionales de testing.

El MP4 que estaba en la carpeta fue eliminado y se agregó `*.mp4` a `.gitignore`.
El video no estaba versionado, por lo que no hay que limpiar historial de Git.

## Ejecutar

Python 3.11 o superior. Solo se requiere NumPy; no se necesita GPU.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Usar el modelo entregado y regenerar evaluación + demo
python -m retail_media evaluate

# Entrenar desde cero y luego evaluar (120 episodios)
python -m retail_media run

# Ejecutar todas las pruebas
python -m unittest discover -s tests -v
```

Opciones útiles:

```bash
python -m retail_media train --episodes 120 --seed 42
python -m retail_media evaluate --eval-seed 30000 --eval-runs 30

# Experimento pequeño; guardar aparte para conservar el modelo entregado
python -m retail_media run --episodes 5 --sessions 100 \
  --artifacts artifacts/smoke --reports reports/smoke

# Cambiar presupuestos o CPC requiere volver a entrenar
python -m retail_media run --config mi_config.json
```

Usa `retail_media/default_config.json` como base para tu configuración. Cambiar
catálogo, CPC, presupuestos o restricciones invalida el fingerprint del modelo:
la carga lo rechaza en lugar de usar una política incompatible.

## Resultado del modelo entregado

Entrenamiento: **120 episodios × 1,000 sesiones**, semilla 42; episodios con
semillas 42–161. Evaluación final: **30,000 sesiones por política**, en 30 días
simulados independientes con semillas **30000–30029**. Las políticas comparten
usuarios, profundidades de scroll y sorteos de respuesta dentro de cada semilla.
La evaluación no actualiza la tabla Q y usa exploración ε = 0.

| Política | CVR por sesión | Cambio vs. orgánico | Entrega diaria media por marca |
|---|---:|---:|---:|
| Solo orgánico | 10.55% | — | 0% |
| Aleatorio + pacing | 8.94% | −1.60 pp | 99.34% |
| Relevancia + pacing | 11.44% | +0.89 pp | 99.57% |
| Q sin entrenar + pacing | 9.05% | −1.50 pp | 99.57% |
| **Q-learning entrenado + pacing** | **10.76%** | **+0.22 pp** | **99.54%** |

El intervalo de confianza del 95% para el cambio del agente frente a orgánico
es **[+0.073, +0.360] puntos porcentuales**. Se calcula sobre las diferencias
emparejadas de los 30 días, usando Student-t conservadora. **No hubo sobregiros**;
las tres marcas superaron el 90% de su cuota diaria en los 30 días de evaluación.
La heurística de relevancia todavía supera al agente: es una referencia fuerte
que debe conservarse para futuras iteraciones.

Estos resultados pertenecen al simulador y **no prueban que el agente mantenga
el CVR de una tienda real**. Las semillas 10000–10019 y 20000–20009 se usaron
durante desarrollo; el conjunto final se ejecutó después de fijar la política.
El entorno de referencia fue Python 3.14.7 / NumPy 2.5.3; otras versiones pueden
introducir pequeñas diferencias numéricas.

## Cómo representa la inversión

| Marca sintética | Inversión de campaña | Duración | Cuota diaria | CPC |
|---|---:|---:|---:|---:|
| Nova | USD 4,000 | 30 días | USD 133.33 | USD 1.20 |
| Casa | USD 2,500 | 30 días | USD 83.33 | USD 1.00 |
| Pulse | USD 1,500 | 30 días | USD 50.00 | USD 0.80 |

Cada episodio representa **un día independiente**, con presupuesto reiniciado
para entrenar. La cuota se calcula como `budget_cents // campaign_days`, por
lo que hay un pequeño residuo de redondeo y de CPC indivisible. Los 30 días de
evaluación son réplicas independientes del mismo día; **no se implementa todavía
una campaña de 30 días con deuda y saldo transferidos entre fechas**.

El objetivo mínimo configurable es entregar el 90% de la cuota diaria; no es
un contrato de impresiones. El pacing vigila gasto entregado frente al avance
del tráfico, evita consumir toda la inversión al inicio y, si una marca va
atrasada, restringe las acciones a productos suyos que aún caben en presupuesto.
El agente aprende cuál de esos productos conviene al usuario.

**Aparecer no equivale a gastar:** una impresión sin clic cuesta USD 0. El sistema
puede exigir exposición, pero no puede forzar clics. Si faltan tráfico,
relevancia o productos, puede quedar inversión sin entregar. El reporte muestra
el cumplimiento por marca y la frecuencia de intervención del pacing; no oculta
ese conflicto rellenando gasto artificialmente.

## Formulación del aprendizaje

El entorno avanza por las ocho oportunidades patrocinables de cada bloque y
contabiliza también las conversiones de las otras doce posiciones orgánicas.
Una sesión visita 1, 2 o 3 bloques según una distribución sintética de abandono.
Esta truncación permite entrenar episodios finitos sobre un patrón de scroll
que se repite indefinidamente en una implementación real.

**Observación:** intención del usuario, grupo de posiciones, profundidad,
fatiga publicitaria, fase del día y marca más atrasada.

**Estado aprendido:** `(intención, profundidad agrupada)`, seis estados. Se
comparte experiencia entre posiciones porque las compras son escasas. Las
demás variables afectan el simulador, las máscaras y el pacing, pero no crean
filas Q adicionales. Esta abstracción no es un estado Markov completo: es una
aproximación deliberada del MVP, sin garantías de convergencia óptima.

**Acciones:** 0 conserva el orgánico; 1–18 eligen productos patrocinados. Las
acciones imposibles por saldo, repetición o pacing se excluyen antes de decidir.
La referencia solo-orgánico ignora expresamente los compromisos comerciales.
Las cuatro políticas comerciales comparten el mismo controlador de pacing.

**Recompensa por oportunidad:**

```text
r = (100 + λ_CVR) × compra
    + (0.20 + 4 × atraso_de_marca) × gasto_CPC_en_USD

Al terminar el día:
r_final -= 4 × promedio(max(0, 0.90 − proporción_de_presupuesto_entregada))

λ_CVR ← clip(λ_CVR + 200 × (CVR_orgánico − CVR_agente − tolerancia), 0, 200)
```

`compra` es una observación binaria, posterior a un clic; se simulan tanto
clics como compras. La recompensa de compra por producto es una señal densa
aproximada para el objetivo de conversión de sesión. **CVR web siempre se evalúa
como sesiones con ≥1 compra / sesiones**, no como compras / impresiones.
También se exportan CVR por impresión, CTR patrocinado y tasa de ocupación.

La tabla se actualiza con Q-learning, α = 0.01, γ = 0.8 y exploración epsilon-greedy
de 0.95 a 0.10 durante entrenamiento. La penalización adaptativa es empírica:
**no es CPO ni una restricción dura de CVR**. En simulación se dispone de una
referencia orgánica emparejada para ajustar λ; en producción esto requiere un
holdout orgánico aleatorizado y no se puede reconstruir directamente de logs.
La política nunca recibe probabilidades verdaderas de clic o compra ni la
respuesta que habría tenido una acción no ejecutada.

## Usar la política desde Python

```python
from retail_media.agent import QAgent
from retail_media.config import load_config
from retail_media.environment import RetailMediaEnv

config = load_config()
agent = QAgent.load("artifacts/model.npz", config, seed=2026)
env = RetailMediaEnv(config, seed=2026)

while not env.done:
    action = agent.act(env.state(), env.allowed_actions(), epsilon=0)
    next_state, reward, info = env.step(action)

print(env.metrics())
```

## Archivos de la entrega

| Archivo | Contenido |
|---|---|
| `retail_media/default_config.json` | Presupuestos, CPC y parámetros editables |
| `retail_media/environment.py` | Tráfico, respuestas, grid, saldo y pacing |
| `retail_media/agent.py` | Q-learning y persistencia sin pickle |
| `retail_media/experiment.py` | Entrenamiento, políticas y evaluación emparejada |
| `retail_media/reporting.py`, `report.html` | Exportación y plantilla de demo |
| `artifacts/model.npz` | Modelo entrenado + metadatos y fingerprint |
| `artifacts/training.csv`, `training.json` | Curvas de los 120 episodios |
| `reports/evaluation.json` | Métricas completas, catálogo y trazas de ejemplo |
| `reports/evaluation.csv` | 150 registros: 5 políticas × 30 días |
| `reports/demo.html` | Reporte autónomo con grid y carga progresiva |
| `tests/test_mvp.py` | Pruebas de reglas, Q-learning y evaluación |

La demo carga bloques de las primeras 12 sesiones registradas por política.
Es una **reproducción finita de decisiones reales del modelo**, no inferencia
en JavaScript ni un frontend conectado a una tienda. El simulador Python sí
genera tráfico nuevo y ejecuta la política cuando se usa `evaluate` o la API.

## Límites y siguiente entrega

- Respuestas simplificadas: la relevancia, posición y fatiga afectan clics y
  compras; la profundidad de scroll se fija antes de actuar. No se modela todavía
  abandono causado por publicidad, repetición entre sesiones ni atribución real.
- Mismo catálogo disponible para todas las sesiones; sin inventario, búsquedas
  libres, frecuencia por usuario ni datos personales.
- Pacing puede imponer anuncios que reduzcan conversión. Si inversión y CVR
  son incompatibles, se debe reportar inviabilidad, ampliar tráfico/plazo o
  renegociar objetivos; no existe una política que garantice ambas cosas siempre.
- La validación real requiere tráfico aleatorizado, intervalos y un criterio
  de no inferioridad de CVR acordado antes del experimento, además de control
  de inversión. El objetivo aquí tiene tolerancia cero en media simulada.
- La siguiente iteración puede usar logs reales, un modelo de respuesta
  calibrado, campañas con saldo continuo y un estado más completo; DQN/PPO
  solo se justifican cuando aumente la dimensión del problema.

Referencias conceptuales: [Watkins y Dayan, Q-learning (1992)](https://www.gatsby.ucl.ac.uk/~dayan/papers/cjch.pdf)
y [Achiam et al., Constrained Policy Optimization (2017)](https://proceedings.mlr.press/v70/achiam17a.html).
Se implementa Q-learning con un controlador operativo propio; no se implementa CPO.
