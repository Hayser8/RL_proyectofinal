# Retail media con aprendizaje por refuerzo

Simulador de retail media en evolución: un agente **Q-learning** elige qué
producto patrocinado mostrar en un grid de posiciones comerciales. Busca
equilibrar valor de conversión, ingreso por **CPC**, CVR web y entrega de
inversión por campaña mediante pacing. Todo el tráfico, catálogo, marcas y
comportamiento son sintéticos.

**Demo lista para abrir:** [reports/demo.html](reports/demo.html). Descarga el
repositorio y abre ese archivo en tu navegador: funciona sin servidor, internet
ni instalación de Python. GitHub muestra el código del HTML, no ejecuta la demo.

## Estado operativo del proyecto

Esta sección organiza el proyecto con una estructura **inspirada en ITIL**:
define el servicio, su estado, evidencias, riesgos y trabajo pendiente. No es
una certificación ITIL; es una bitácora operativa para que el equipo pueda
presentar y continuar el proyecto sin perder contexto.

### Servicio y objetivo

| Elemento | Estado actual |
|---|---|
| Servicio | Simulador reproducible de retail media con aprendizaje por refuerzo. |
| Decisión automatizada | Conservar contenido orgánico o escoger uno de 18 productos patrocinados en los spots 3–6 y 11–14. La posición 1 permanece orgánica. |
| Objetivo comercial | Equilibrar valor de conversión, ingreso CPC, relevancia, CVR y entrega de inversión; **mayor CPC no garantiza mejor posición**. |
| Técnica | Q-learning tabular con acciones enmascaradas, pacing y evaluación emparejada. |
| Datos | Catálogo, usuarios, clics, compras y presupuestos completamente sintéticos. |
| Versión del modelo actual | Esquema `intent_position_depth_v3`, 120 episodios, semilla de entrenamiento 42. |
| Estado técnico | Operativo y reproducible: 35/35 pruebas automatizadas pasan. |
| Estado de calidad | Ámbar: el modelo RL v3 entrega presupuesto sin sobregiros, pero todavía no demuestra no-inferioridad de CVR frente al baseline orgánico. |

### Registro de configuración y cambios

| Cambio | Estado | Impacto |
|---|---|---|
| Pacing y presupuesto CPC | Implementado | Evita sobregiros y recupera inversión pendiente. |
| Campaña continua | Implementado | Arrastra saldo no gastado entre días y soporta días sin tráfico. |
| Multiplicadores de posición | Implementado | Las ubicaciones superiores tienen más visibilidad simulada. |
| Valor de conversión por marca | Implementado | Distingue una venta de alto y bajo valor en la recompensa. |
| Estado Q sensible a posición | Implementado | RL distingue grupo de posiciones 3–6 de 11–14. |
| Baselines `bid` y `rotation` | Implementado | Permiten contrastar pago máximo, distribución y RL. |
| Reporte de distribución marca × posición | Implementado | La demo muestra `Mayor CPC` frente a RL por cada spot. |
| Reentrenamiento final v3 | Ejecutado | Modelo y reportes regenerados con semillas separadas. |
| Historial de prompts | Fuera del código por decisión del equipo | Debe elaborarse colaborativamente para el documento final. |

## Qué incluye

- Bloques de **20 productos**; únicamente los spots **3, 4, 5, 6, 11, 12, 13 y 14**
  admiten patrocinados. La posición 1 siempre es orgánica; la numeración se
  repite por bloque.
- Tres intenciones/categorías, tres marcas y 18 productos patrocinados.
- Acción de conservar el orgánico o elegir un producto patrocinado.
- Multiplicadores de visibilidad por posición patrocinada y valor de conversión
  por campaña; la posición 3 es más visible que la 14.
- Comparadores de decisión: orgánico, aleatorio, relevancia, mayor CPC,
  rotación, Q sin entrenar y Q-learning.
- Presupuestos monetarios en centavos, cobro solo por clic, prevención de
  sobregiros y de patrocinados duplicados en un mismo bloque.
- Pacing que limita adelantos y exige oportunidades para marcas atrasadas.
- Campañas de varios días con saldo continuo, recuperación de inversión pendiente
  y tráfico variable, incluidos días sin visitas.
- Modelo guardado, curvas de entrenamiento, siete políticas de comparación,
  exportaciones CSV/JSON y una demo que reproduce decisiones del modelo.
- 35 pruebas automatizadas sin dependencias adicionales de testing.

El MP4 que estaba en la carpeta fue eliminado y se agregó `*.mp4` a `.gitignore`.
El video no estaba versionado, por lo que no hay que limpiar historial de Git.

## Ejecutar la demo y reproducir el experimento

### Demo sin instalar nada

1. Descarga o clona el repositorio completo para conservar `reports/`,
   `artifacts/` y el catálogo de resultados.
2. Abre [reports/demo.html](reports/demo.html) desde el explorador de archivos
   o con cualquier navegador moderno.
3. En el selector **Política**, compara `Mayor CPC`, `Relevancia`, `Rotación` y
   `Agente entrenado`; luego revisa la sección **Distribución por posición**.

El HTML es autónomo: no abre un servidor, no necesita internet y reproduce
trazas finitas guardadas. No calcula nuevas decisiones dentro del navegador.

### Windows PowerShell

```powershell
# Desde la raíz del repositorio
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# Evita problemas de caracteres como ε y Δ en algunas consolas Windows
$env:PYTHONUTF8 = "1"

# Validación completa
python -m unittest discover -s tests -v

# Reutiliza artifacts/model.npz y regenera reports/evaluation.* + reports/demo.html
python -m retail_media evaluate --eval-seed 30000 --eval-runs 30

# Abre la demo local
Start-Process reports\demo.html
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
PYTHONUTF8=1 python -m unittest discover -s tests -v
PYTHONUTF8=1 python -m retail_media evaluate --eval-seed 30000 --eval-runs 30
open reports/demo.html  # macOS; usa xdg-open en Linux
```

### Operaciones reproducibles

| Objetivo | Comando | Efecto |
|---|---|---|
| Validar código | `python -m unittest discover -s tests -v` | Ejecuta las 35 pruebas. |
| Evaluar modelo actual | `python -m retail_media evaluate --eval-seed 30000 --eval-runs 30` | Regenera JSON, CSV y demo desde el modelo guardado. |
| Entrenar y evaluar desde cero | `python -m retail_media run --episodes 120 --seed 42 --eval-seed 30000 --eval-runs 30` | Sobrescribe `artifacts/` y `reports/` con un experimento reproducible. |
| Campaña continua | `python -m retail_media campaign` | Genera saldo acumulado y reporte diario. |
| Probar mayor CPC | `python -m retail_media campaign --policy bid` | Ejecuta la campaña con el ranking de CPC. |
| Probar rotación | `python -m retail_media campaign --policy rotation` | Ejecuta la campaña con reparto de impresiones. |

> **Control de cambio:** entrenar con una configuración distinta cambia el
> fingerprint y vuelve incompatible el modelo anterior por diseño. Guarda los
> resultados actuales en una rama, commit o carpeta separada antes de experimentar.

## Referencia rápida de CLI

Python 3.11 o superior. Solo se requiere NumPy; no se necesita GPU.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Evaluar requiere un modelo entrenado con la configuración y esquema actuales
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

# Campaña completa con saldo continuo y el modelo ya entrenado
python -m retail_media campaign

# Caso de recuperación: primer día sin visitas y luego tráfico variable
python -m retail_media campaign --traffic-file config/campaign_traffic.json

# Comparar una campaña usando únicamente mayor CPC o rotación de marcas
python -m retail_media campaign --policy bid
python -m retail_media campaign --policy rotation

# Experimento pequeño; guardar aparte para conservar el modelo entregado
python -m retail_media run --episodes 5 --sessions 100 \
  --artifacts artifacts/smoke --reports reports/smoke

# Cambiar campañas, multiplicadores o el esquema requiere volver a entrenar
python -m retail_media run --config mi_config.json
```

Usa `retail_media/default_config.json` como base para tu configuración. Cambiar
catálogo, CPC, presupuestos, valor de conversión, posiciones o restricciones invalida el fingerprint del modelo:
la carga lo rechaza en lugar de usar una política incompatible.

## Resultados: referencia previa y evaluación v3

La siguiente evaluación pertenece al modelo anterior, que no distinguía grupos
de posición en su tabla Q ni usaba valor de conversión. Se conserva como
referencia del MVP, **no** como resultado de la versión actual. El esquema
`intent_position_depth_v3` rechaza deliberadamente el artefacto anterior; al
finalizar los cambios de posicionamiento se entrenó y evaluó un modelo nuevo
con semillas separadas, reportado a continuación.

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

### Evaluación final del esquema v3

La evaluación actual usa el modelo `intent_position_depth_v3`, entrenado durante
**120 episodios × 1,000 sesiones** (semillas 42–161). Evalúa **30,000 sesiones
por política** en las semillas 30000–30029, con tráfico y sorteos emparejados.
Incluye valor de conversión, multiplicadores de posición y los comparadores
`bid` y `rotation`.

| Política | CVR por sesión | Cambio vs. orgánico | IC 95% del cambio | Entrega media por marca |
|---|---:|---:|---:|---:|
| Solo orgánico | 10.55% | — | — | 0% |
| Aleatorio + pacing | 9.05% | −1.50 pp | [−1.66, −1.34] pp | 99.49% |
| Relevancia + pacing | **11.78%** | **+1.23 pp** | [+1.08, +1.38] pp | 99.57% |
| Mayor CPC + pacing | 9.22% | −1.33 pp | [−1.51, −1.15] pp | 99.57% |
| Rotación + relevancia | 10.41% | −0.13 pp | [−0.29, +0.03] pp | 99.57% |
| Q sin entrenar + pacing | 9.09% | −1.45 pp | [−1.67, −1.24] pp | 99.52% |
| Q-learning v3 + pacing | 10.37% | −0.18 pp | [−0.40, +0.04] pp | 99.57% |

No hubo sobregiros en ninguna política. El comparador `bid`, que privilegia el
CPC de Nova, pierde 1.33 pp de CVR: evidencia que pagar más no debe bastar para
asignar un espacio visible. La política RL obtiene mejor CVR y valor de
conversión que `bid`, `random` y Q sin entrenar, pero **no demuestra aún
protección de CVR frente al baseline orgánico**, y relevancia supera sus
resultados. Esta es una conclusión negativa válida del experimento: antes de
usar RL en producción se debe ajustar la función de recompensa/estado y repetir
la evaluación retenida, en vez de afirmar una mejora no demostrada.

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

Cada episodio de entrenamiento y cada réplica de `evaluate` representa **un día
independiente**, con cuota `budget_cents // campaign_days`. El comando nuevo
`campaign` ejecuta una campaña completa con saldo continuo: lo no gastado se
arrastra a los días siguientes y el último día recupera también el redondeo.
Los resultados diarios originales y la demo HTML conservan su significado.

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

## Avance: campaña con saldo continuo

Antes, un día con pocas visitas perdía su oportunidad de entregar inversión:
el siguiente día empezaba nuevamente con la misma cuota independiente. Ahora
el límite de cada marca se calcula a partir de su gasto **acumulado**:

```text
meta_acumulada = presupuesto_total × día // días_de_campaña
asignación_del_día = meta_acumulada − gasto_acumulado
```

La meta del último día equivale al presupuesto completo. Cada clic debe caber
en la asignación antes de mostrarse el anuncio. El cierre del día valida el
gasto y solo después actualiza el saldo; un cierre inválido no altera el ledger.
La secuencia impide abrir otro día antes de cerrar el actual.

`config/campaign_traffic.json` contiene una lista de sesiones para cada uno de
los 30 días. Admite cero para simular una caída de la web o una jornada sin
visitas. Esos días no generan cobros ni un CVR ficticio: su CVR se reporta `null`.
El CVR de campaña se calcula con **todas las sesiones**, sin promediar porcentajes
de días con volúmenes diferentes. Si toda la campaña tiene cero visitas, su CVR
también es `null` y se informa la falta de entrega.

Ejemplo incluido, semilla 40000, **31,200 sesiones** y primer día sin tráfico:

| Marca | Presupuesto | Gasto acumulado final | Saldo pendiente |
|---|---:|---:|---:|
| Nova | USD 4,000.00 | USD 3,999.60 | USD 0.40 |
| Casa | USD 2,500.00 | USD 2,500.00 | USD 0.00 |
| Pulse | USD 1,500.00 | USD 1,500.00 | USD 0.00 |

El atraso inicial se recupera durante los días siguientes. El único saldo final,
USD 0.40 de Nova, es menor a su CPC de USD 1.20 y no permite comprar otro clic.
No se inventa gasto para completar ese residuo. **No hubo sobregiros**.
El CVR de esta trayectoria fue **10.70%** frente a **10.59%** de su referencia
orgánica emparejada; es una sola campaña y no constituye evidencia estadística
de mejora. Sus días dependen del saldo anterior y no se tratan como 30 réplicas
independientes para calcular un intervalo de confianza.

Se utiliza la política existente congelada, entrenada sobre días independientes:
no se volvió a entrenar ni se alteró `artifacts/model.npz`. El nuevo controlador
le asigna el saldo actualizado. Se puede comparar con las políticas `relevance`,
`random` u `organic` usando `--policy`; cada una genera archivos separados.

Los reportes `reports/campaign-rl.json` y `reports/campaign-rl.csv` incluyen gasto
diario, meta acumulada, gasto acumulado, atraso y saldo por marca. Un saldo mayor
que el CPC queda señalado como inversión pendiente, aunque alcance el mínimo
de entrega; no se confunde cumplimiento mínimo con consumo completo.

## Formulación del aprendizaje

El entorno avanza por las ocho oportunidades patrocinables de cada bloque y
contabiliza también las conversiones de las otras doce posiciones orgánicas.
Una sesión visita 1, 2 o 3 bloques según una distribución sintética de abandono.
Esta truncación permite entrenar episodios finitos sobre un patrón de scroll
que se repite indefinidamente en una implementación real.

**Observación:** intención del usuario, grupo de posiciones patrocinadas,
profundidad, fatiga publicitaria, fase del día y marca más atrasada. Los grupos
de posición son 3–6 y 11–14; cada posición conserva además su propio
multiplicador de visibilidad.

**Estado aprendido:** `(intención, grupo_de_posición, profundidad agrupada)`,
doce estados. Así el agente puede aprender valores diferentes para ubicaciones
de mayor y menor visibilidad sin multiplicar innecesariamente la tabla por cada
variable operativa. Fatiga, fase y pacing afectan el simulador y las máscaras,
pero no crean filas Q adicionales. Esta abstracción no es un estado Markov
completo: es una aproximación deliberada, sin garantías de convergencia óptima.

**Acciones:** 0 conserva el orgánico; 1–18 eligen productos patrocinados. Las
acciones imposibles por saldo, repetición o pacing se excluyen antes de decidir.
La referencia solo-orgánico ignora expresamente los compromisos comerciales.
Los seis comparadores comerciales comparten el mismo controlador de pacing.

**Recompensa por oportunidad:**

```text
r = valor_de_conversión_en_USD
    + (0.20 + 4 × atraso_de_marca) × ingreso_CPC_en_USD
    + λ_CVR × compra

Al terminar el día:
r_final -= 4 × promedio(max(0, 0.90 − proporción_de_presupuesto_entregada))

λ_CVR ← clip(λ_CVR + 200 × (CVR_orgánico − CVR_agente − tolerancia), 0, 200)
```

`compra` es una observación binaria, posterior a un clic; se simulan tanto
clics como compras. El valor de conversión se acredita únicamente cuando existe
una compra patrocinada y el ingreso CPC únicamente cuando existe clic. El
desglose de recompensa queda registrado por decisión para poder auditar cuánto
provino de conversión, CPC, protección de CVR o penalización de entrega. **CVR
web siempre se evalúa como sesiones con ≥1 compra / sesiones**, no como compras
/ impresiones. También se exportan CVR por impresión, CTR patrocinado y tasa de
ocupación.

La tabla se actualiza con Q-learning, α = 0.01, γ = 0.8 y exploración epsilon-greedy
de 0.95 a 0.10 durante entrenamiento. La penalización adaptativa es empírica:
**no es CPO ni una restricción dura de CVR**. En simulación se dispone de una
referencia orgánica emparejada para ajustar λ; en producción esto requiere un
holdout orgánico aleatorizado y no se puede reconstruir directamente de logs.
La política nunca recibe probabilidades verdaderas de clic o compra ni la
respuesta que habría tenido una acción no ejecutada.

## Comparadores y evidencia de equilibrio

La evaluación ejecuta todas las políticas sobre el mismo tráfico y los mismos
sorteos aleatorios en cada semilla. Así una diferencia no se atribuye a que una
política recibió usuarios más favorables.

| Política | Regla de decisión | Qué permite comprobar |
|---|---|---|
| `bid` | El CPC más alto elegible; desempata por identificador de producto | El pago por sí solo puede favorecer un producto irrelevante. |
| `relevance` | Mayor coincidencia con la intención y calidad de producto | El valor para el usuario sin considerar quién paga más. |
| `rotation` | Marca con menos impresiones; luego relevancia | Distribución equilibrada de exposición entre marcas. |
| `rl` | Valores Q aprendidos por intención, grupo de posición y profundidad | El equilibrio aprendido entre valor de conversión, CPC, CVR y pacing. |

Además de CVR, CTR, entrega y sobregiros, cada evaluación exporta la matriz
`position_brand_impressions`: filas por marca y columnas para los spots 3, 4,
5, 6, 11, 12, 13 y 14. Esta matriz será la evidencia central para responder
si una marca con mayor CPC monopoliza las posiciones más visibles o si el
agente la distribuye según relevancia y valor esperado. El comparador `bid`
está probado para elegir el CPC más alto incluso cuando su categoría no
coincide con la intención del usuario; no se presenta como una política deseable.

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
| `retail_media/default_config.json` | Presupuestos, CPC, valor de conversión y multiplicadores de posición |
| `retail_media/environment.py` | Tráfico, respuestas, grid, saldo, pacing y valor comercial por decisión |
| `retail_media/agent.py` | Q-learning sensible al grupo de posición y persistencia sin pickle |
| `retail_media/experiment.py` | Entrenamiento, comparadores y evaluación emparejada con distribución por posición |
| `retail_media/campaign.py` | Saldo continuo, recuperación de atrasos y evaluación de campaña |
| `config/campaign_traffic.json` | Escenario de tráfico diario, incluido un día sin visitas |
| `retail_media/reporting.py`, `report.html` | Exportación y plantilla de demo |
| `artifacts/model.npz` | Modelo entrenado + metadatos y fingerprint |
| `artifacts/training.csv`, `training.json` | Curvas de los 120 episodios |
| `reports/evaluation.json` | Métricas completas, catálogo y trazas de ejemplo |
| `reports/evaluation.csv` | 210 registros: 7 políticas × 30 días, incluidas métricas comerciales y distribución por posición |
| `reports/campaign-rl.json`, `campaign-rl.csv` | Trayectoria completa: 30 días y saldo acumulado por marca |
| `reports/demo.html` | Reporte autónomo con grid y carga progresiva |
| `tests/test_mvp.py` | Pruebas de reglas, Q-learning y evaluación |
| `tests/test_campaign.py` | Arrastre de saldo, cero tráfico, redondeo y evaluación de campaña |

La demo carga bloques de las primeras 12 sesiones registradas por política.
Es una **reproducción finita de decisiones reales del modelo**, no inferencia
en JavaScript ni un frontend conectado a una tienda. El simulador Python sí
genera tráfico nuevo y ejecuta la política cuando se usa `evaluate` o la API.

## Riesgos, límites y trabajo pendiente

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
  de inversión. El objetivo aquí tiene tolerancia cero en media simulada; la
  evaluación v3 actual no supera esa prueba para RL frente a orgánico.
- La siguiente iteración puede usar logs reales, un modelo de respuesta
  calibrado y reentrenar con un estado que represente la campaña completa; DQN/PPO
  solo se justifican cuando aumente la dimensión del problema.

### Registro de riesgos e incidencias conocidas

| Riesgo / incidencia | Severidad | Estado | Mitigación actual |
|---|---|---|---|
| RL v3 no supera CVR orgánico | Alta para afirmar éxito de RL | Abierto | Reportar el resultado negativo; comparar contra relevancia; ajustar recompensa/estado antes de reclamar mejora. |
| Mayor CPC reduce CVR | Alta para un ranking solo comercial | Demostrado | Mantener `bid` como baseline de control, no como política recomendada. |
| Simulador no representa usuarios reales | Alta para despliegue real | Abierto | No hacer afirmaciones de producción; requerir A/B, holdout orgánico y datos calibrados. |
| Pérdida de presupuesto por falta de clics | Media | Gestionado | Pacing, campaña continua y reporte de saldo residual. |
| Artefacto incompatible tras cambiar configuración | Baja / esperada | Gestionado | Fingerprint y esquema v3 rechazan cargas incompatibles; reentrenar de forma explícita. |
| Caracteres Unicode en consola Windows | Baja | Gestionado | Usar `$env:PYTHONUTF8 = "1"` antes de entrenar o probar. |

Referencias conceptuales: [Watkins y Dayan, Q-learning (1992)](https://www.gatsby.ucl.ac.uk/~dayan/papers/cjch.pdf)
y [Achiam et al., Constrained Policy Optimization (2017)](https://proceedings.mlr.press/v70/achiam17a.html).
Se implementa Q-learning con un controlador operativo propio; no se implementa CPO.
