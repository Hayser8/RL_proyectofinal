# MVP de retail media con RL

Entrega parcial solicitada: simulador sintético reproducible, agente entrenado,
evaluación y demostración de un grid de scroll. El usuario confirmó cobro CPC.

Decisiones de implementación: Python + NumPy; Q-learning tabular para poder
explicar y guardar la política sin GPU. Se descartaron PPO/DQN por complejidad
innecesaria para esta entrega y un bandit porque presupuesto, ritmo de entrega y
fatiga generan dependencia temporal. No se implementa CPO ni se promete una
garantía matemática de restricciones.

Cada bloque tiene 20 posiciones, numeradas desde 1. Solo 3, 4, 5, 6, 11, 12,
13 y 14 admiten publicidad. Siempre se puede conservar un producto orgánico,
excepto cuando el control operativo de pacing exige recuperar una marca atrasada.
El scroll se trunca a 1–3 bloques por sesión para simular abandono y acabar episodios.

Tres marcas, tres categorías y dos productos por categoría/marca. Presupuestos
de campaña de USD 4,000, 2,500 y 1,500, distribuidos en 30 días; se simula un día
por episodio. CPC específico por marca. Solo un clic cuesta dinero; jamás
sobrepasar presupuesto diario o de campaña. Impresión no significa gasto.
El pacing puede exigir exposición a marcas atrasadas, pero no garantiza clics.

Observación: intención de usuario, posición, profundidad, fatiga, fase y marca más
atrasada. La tabla Q agrega el estado a intención y profundidad para compartir
compras escasas entre posiciones; las demás dimensiones afectan las máscaras y
el control operativo. Es una aproximación, no un estado Markov completo.
Acción: orgánico o un producto patrocinado. Recompensa por compra,
gasto CPC entregado y recuperación del pacing; multiplicador adaptativo penaliza
la pérdida de conversión. Las compras se muestrean después del clic. La política
no recibe probabilidades verdaderas del simulador.

CVR web = sesiones con al menos una compra / sesiones. También reportar CVR por
impresión, CTR patrocinado, gasto y cumplimiento diario de cada marca. Comparar
orgánico, aleatorio, relevancia, Q sin entrenar y Q entrenado sobre tráfico y
variables aleatorias emparejados; semillas de evaluación separadas del entrenamiento.
Reportar intervalo de confianza del cambio de CVR y restricciones incumplidas.
Nunca interpretar una simulación favorable como evidencia sobre usuarios reales.

Demo HTML local y autónoma: reproduce decisiones reales del agente guardadas
durante evaluación, con grid y scroll; no inventa inferencias en JavaScript.
Paleta azul tinta, azul claro, blanco y naranja para posiciones patrocinadas;
tipografía de sistema y números monoespaciados, sin servicios externos.

No publicar, desplegar ni modificar servicios externos. Quitar el MP4 solicitado.
