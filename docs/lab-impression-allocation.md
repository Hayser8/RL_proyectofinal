# Competencia y exposición en la misma PLP

## Corrección del caso de uso

La versión anterior contaba18 anuncios globales en cada categoría: solo 6 eran
propios de esa PLP y el filtro podía dejar15 en cero. Eso no representaba la
competencia solicitada. Se reemplazó con tres inventarios disjuntos de 16 anuncios
relevantes. Hay48 perfiles reales en el modelo nuevo, reentrenados con 900,000
transiciones; no son clones de pesos ni contadores decorativos.

Cada producto tiene nombre y fotografía coherentes con su categoría; se utilizan
16 SKUs ya presentes en el catálogo local como productos anunciables. Se evita
ver el mismo SKU dos veces en un bloque. Las imágenes no entran al predictor.

## Primera exposición y balance

El controller `plp16-min1-v1` prioriza la primera exposición de cada anuncio
apto, después concentra por valor de primera compra de sesión y pacing. La
cobertura no añade recompensa, no altera el CVR contabilizado y no usa datos
futuros. Saldo, categoría, duplicados y compra previa se respetan. Si es
inviable, `coverage.pending` lo declara. La demo por defecto y los32 días del
agente evaluados cubren48/48; esto no garantiza cobertura bajo cualquier tráfico
o presupuesto posible.

CPCes capacidad de gasto por clic, no una cuota implícita de impresiones.
El mínimo es un contrato explícito de esta simulación solicitado por el usuario.
No se presenta como una regla universal del sector ni como garantía de que
anuncios dañinos deban mostrarse. La cohorte menor es relevante y puede mejorar
frente a orgánico; pierde prioridad respecto a los mejores candidatos.

Se conserva pacing por marca, gasto real CPC y filtro empírico de compra. No
se asignan cuotas iguales después del mínimo ni se fuerza la distancia entre
las curvas. Los costos de oportunidad de cobertura entran en la evaluación.

Referencias conceptuales consultadas: [Amazon CPC y presupuestos](https://advertising.amazon.com/solutions/products/sponsored-products),
[Amazon puja y relevancia](https://m.media-amazon.com/images/G/01/AmazonMarketingServices/PartnerOnboardingGuide/V3/AMZ_BiddingAndTargettingGuide_HP_KT_V5.pdf),
[Ad Manager contratos de reserva](https://support.google.com/admanager/answer/177279?hl=en).
La guía histórica de Amazon se cita por conceptos, no por límites actuales.

## Winners y losers

Para cada PLP, se calcula Q en una visita nueva, espacio 3, primer bloque, sin
compra ni anuncios anteriores. Se ordenan los16 por soporte del filtro y valor
aprendido: Winners son los8 mejores; Losers losotros8. Es una comparación relativa,
no significa que estos últimos sean malos para toda persona o peores que
orgánico. La clasificación se fija antes de servir; no utiliza puja, presupuesto,
impresiones finales o probabilidades verdaderas del generador.

Los miembros pertenecen a la misma PLP y cada anuncio aparece en un solo grupo.
Las curvas incluyen todos sus eventos de esa categoría y todos los bloques.
El promedio divide por 8, incluyendo miembros con cero exposición si la cobertura
fuese inviable. La mejora deQ es una predicción en un contexto de referencia,
no CVR causal de una cohorte; una visita puede contener ambos grupos.

Réplica descriptiva de semilla 91031,1000 visitas previstas por escenario:

| PLP equilibrada | Winners | Losers | Menor número de impresiones de cualquier anuncio |
|---|---:|---:|---:|
|Tecnología|1057|543|12|
|Hogar|871|464|35|
|Deporte|482|229|18|

Son datos del motor, no una curva impuesta. La evaluación de 8 semillas se guarda
por separado. El esquema v3 y la identidad del modelo/controller se verifican al
servir los reportes.

## Contabilidad y valoración

Por anuncio y oportunidad: considerados=aptos+excluidos;
aptos = impresiones + pérdidas por ranking + pérdidas por recuperación de pacing + pérdidas por cobertura inicial.
La exclusión tiene una causa principal para evitar contar dos veces: visita
convertida, política, saldo, SKUduplicado, cap de pacing o filtro. Pueden
coexistir otras causas. Las impresiones solo se cuentan al ejecutar la vista;
los clics y el gasto reconcilian con el ledger por marca. La serie comienza en0
y registra visitas cerradas, con unos100 checkpoints acotados por categoría.

**Rúbrica técnica propia:** representación25, aprendizaje25, controles20,
cobertura20 y explicación10. Antes55/100; actual88/100. No es precisión
estadística. Los32 días con cobertura y los controles apoyan la calificación,
pero los puntos incluyen juicio profesional explícito. No hay evidencia de
producción, garantía formal de CVR ni superioridad concluyente frente a políticas
fuertes. El detalle se muestra en Modelo y `assessment` del reporte JSON.

```bash
python3 -m retail_media.lab_competition
```

Genera `reports/lab_competition.json`, con series reales, mínimo por anuncio,
causas de exclusión y valoración. Requiere el modelo y evaluación compatibles
para completar la calificación. Los antecedentes están en `reports/archive/lab-v1/`.
