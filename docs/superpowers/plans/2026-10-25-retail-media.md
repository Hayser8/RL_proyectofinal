# Retail media RL — Implementation Plan

**Goal:** Entregar un MVP entrenado, reproducible y explicable con cobro CPC.
**Architecture:** Simulador separado de Q-learning, evaluación y reporte HTML.
**Tech Stack:** Python >=3.11, NumPy; unittest y HTML/CSS/JS sin dependencias web.
**Spec:** docs/superpowers/specs/2026-10-25-retail-media-design.md

## Restricciones globales

20 productos/bloque; spots 3,4,5,6,11,12,13,14; CPC; presupuestos en centavos;
semillas reproducibles; CVR por sesión; sin acceso de la política a probabilidades
verdaderas. La demo muestra reproducción de simulación.

## Riesgos a verificar

Presupuesto menor a un clic; CPC sin clic; acciones no válidas; semillas y modelos
incompatibles; ausencia de tráfico; evaluación no confunde oportunidades con exposición.

## Tareas

- [x] 1. Escribir y ejecutar tests de configuración, spots, CPC, presupuesto,
  reproducción de tráfico y cierre de episodios; implementar `config.py`, `environment.py`.
- [x] 2. Escribir y ejecutar tests de actualización Q, máscara y persistencia;
  implementar `agent.py`, entrenamiento y políticas de comparación.
- [x] 3. Escribir y ejecutar tests de evaluación emparejada y reporte;
  implementar CLI, CSV/JSON, curvas de entrenamiento y demo HTML.
- [x] 4. Entrenar, evaluar en semillas nuevas, inspeccionar demo y documentar
  comandos, resultados y límites; ejecutar suite completa y verificar procesos.

Las tareas se realizan en la sesión actual y rama main, por instrucción explícita
del usuario. Al terminar se harán commits y push al remoto origin.
El repositorio no contiene código previo. Se revisa el diff al terminar.

## Registro de ejecución y verificación

- Primer modelo: demasiados estados y actualizaciones ruidosas de compras
  escasas. Se adoptó agregación intención/profundidad, α=0.01 y γ=0.8; test de
  compartir experiencia observado en rojo y luego verde.
- Modelo final: 120 episodios; conjunto de desarrollo 20000–20009 y evaluación
  final independiente 30000–30029. No se cambió la política después del test final.
- CVR final 10.7633% frente a 10.5467% orgánico; IC 95% del cambio
  [+0.07296, +0.36038] pp. Entrega media 99.54%, sin sobregiros.
- `python3 -m unittest discover -s tests -v`: 17/17 pasan.
- `python3 -m compileall -q retail_media tests`: correcto.
- Revisión independiente `/root/review_mvp`: sin hallazgos bloqueantes; sugerencia
  de versionado de esquema corregida con test rojo→verde y formato v2.
- Demo inspeccionada en navegador de escritorio y viewport móvil 390 px:
  sin overflow, cambio a orgánico elimina patrocinados y carga de más bloques
  conserva 20 productos por bloque. Pestaña temporal cerrada al terminar.
- Sesiones de entrenamiento/evaluación 90250, 6799 y 82179 terminaron con exit 0.
  PID de evaluación 11943 ya no existe. Sin servidores de preview iniciados.
