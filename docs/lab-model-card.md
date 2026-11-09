# Modelo PLP16: ficha técnica

Versión activa: `retail_lab_transition_v2_plp16`; controller `plp16-min1-v1`.
Modelo basado en transiciones empíricas y planificación de Bellman, horizonte
finito de hasta tres bloques. No es una red neuronal ni el Q-learning histórico.

## Inventario y entrenamiento

Tres PLP: Tecnología, Hogar y Deporte. Cada una tiene **16 anuncios propios**;
48 acciones patrocinadas y una acción orgánica. En cada bloque de 20 productos,
solo 3, 4, 5, 6, 11, 12, 13 y 14 admiten publicidad. Entrenamiento: **900,000 transiciones
factuales**, semilla 1700; validación3000 eventos con semilla 2700. Se muestrea
solo entre orgánico y los16 anuncios de la categoría del estado. Las celdas de
otras categorías no se usan como candidatos ni se rellenan con etiquetas oráculo.

Cada anuncio posee parámetros sintéticos de respuesta diferentes (marca,
variante, exposición, clic, compra y abandono). Los parámetros verdaderos solo
pertenecen al generador privado; el modelo observa la respuesta de la acción
ejecutada. Los48 perfiles se reentrenaron desde cero. Las fotografías y precios
de venta no son señales de entrada. Se reutilizan16 SKUs anunciables existentes
por categoría, también comprables orgánicamente; no se afirma haber generado
48 imágenes nuevas. El grid conserva20 SKUs distintos por bloque mediante swaps
de productos pendientes y una máscara de SKUs ya observados.

## Recompensa y entrega

Recompensa1 solo para primera compra por sesión, tanto orgánica como patrocinada.
Compras adicionales, impresiones, clics, pujas y gasto no dan recompensa.
La inferencia es congelada. Cada campaña diaria conserva los presupuestos base
por marca: NovaUSD133.33,CasaUSD83.33,PulseUSD50.00; CPCfijoUSD1.20,1.00,0.80.
Solo un clic patrocinado se cobra; saldo, repetición y categoría son máscaras.
No es una subasta industrial con precios de equilibrio.

El filtro de `safe_rl` y `greedy` exige100 observaciones y estimación de compra
inmediata menos1 desviación estándar no inferior al orgánico puntual. No es una
cota95% ni garantía formal del CVR. Las futuras máscaras de saldo/duplicados
se aproximan en la planificación; las del espacio actual se aplican exactamente.

**Cobertura mínima real:** entre candidatos aptos no expuestos aún en el día,
el controlador da una primera impresión antes de concentrarse en el mayor Q.
No ignora saldo, duplicados ni una sesión ya convertida. No permite entrar a
un producto ajeno a la PLP. Después de la cobertura usa valor de conversión y
recuperación de pacing de marca, con cap de adelanto. La primera exposición es
un costo de oportunidad incluido en CVR y ledger. Sin tráfico, saldo o soporte
no se puede garantizar cobertura: se declara pendiente y no se inventan eventos.

Los16 anuncios de cada inventario son relevantes; los menos favorecidos tienen
menor valor que los mejores, sin necesidad de ser inferiores al orgánico. El
escenario clickbait degrada respuesta real de ciertos anuncios respecto del
entrenamiento y prueba esta limitación del modelo congelado.

## Evaluación reproducible

Semillas80020–80027, cuatro escenarios, siete políticas:224 ejecuciones.
1000 visitas previstas por día; tráfico escaso usa22%. Usuarios y sorteos
exógenos se comparten entre políticas; abandono puede cambiar la trayectoria.
CVRcuenta solo sesiones cerradas. Intervalos95% usan diferencias por día
independiente con Student-t, no impresiones independientes.

| Escenario | CVR agente | Orgánico | Diferencia, pp | IC95%, pp | Entrega media |
|---|---:|---:|---:|---:|---:|
| Equilibrado |14.14%|11.59%|+2.55|[+2.176,+2.924]|99.57%|
| Clics sin intención |13.06%|11.59%|+1.475|[+1.141,+1.809]|99.57%|
| Tráfico escaso |18.30%|10.74%|+7.557|[+5.932,+9.181]|59.19%|
| Cambio de demanda |13.66%|11.59%|+2.075|[+1.664,+2.486]|99.57%|

Los intervalos frente a `quality` y `greedy` incluyen cero en los cuatro
escenarios: **no se demuestra superioridad de RL frente a esas referencias**.
Se observó cobertura de 48/48 anuncios en32/32 días del agente, incluso con tráfico
escaso. No hubo sobregiros en224 ejecuciones. Nueve probes dirigidos pasan
(clic sin compra, simetría, recompensa única, saldo cero, congelación, ausencia
de futuro, fallback, cota por sesión y proxy financiero). No prueban ausencia
universal de reward hacking ni CVR de producción.

La evaluación guarda identidad SHA256 del modelo y `serving_id`. La API rechaza
reportes de otro modelo o controller; el reporte de clusters exige esquema v3.
Las cifras v1 se conservan en `reports/archive/lab-v1/` y el modelo anterior en
`artifacts/archive/lab_model_v1.npz`. El catálogo/generador v1 era diferente:
no comparar porcentajes viejos y nuevos como si fueran un A/B causal.

## Clusters, cobertura y calificación

[Metodología de impresiones](lab-impression-allocation.md): dos cohortes fijas
de 8 anuncios de la misma PLP, definidas por Q aprendido antes de servir.
No se usa la puja ni la exposición final para fabricar winners. El gráfico
suma eventos ejecutados y ofrece promedio por todos los miembros. Se incluyen
exclusiones, mínimo observado y gasto de la misma réplica.

La calificación **88/100** es una rúbrica técnica propia para la demostración,
frente a55/100 de adecuación anterior. No es accuracy ni una certificación.
Los pesos, puntos y limitaciones están expuestos en Modelo y en el JSON. Los
componentes de aprendizaje, controles y explicabilidad incluyen juicio técnico;
la cobertura y consistencia de inventario se verifican con eventos.

## Reproducción y recursos

```bash
python3 -m retail_media train-lab --lab-observations 900000
python3 -m retail_media evaluate-lab --lab-sessions 1000 --lab-runs 8
python3 -m retail_media.lab_competition
python3 -m unittest discover -s tests -q
node tests/test_lab_clusters.cjs
node tests/test_lab_lesson.cjs
node tests/test_catalogue_images.cjs
python3 -m retail_media lab
```

El servidor se enlaza a127.0.0.1, máximo12 simulaciones con TTLde1 hora, avances
acotados a200 decisiones y JSONde32 KiB, restricción de origen y archivos públicos.
No incorpora autenticación para exposición a internet. Detener con Ctrl+C.
