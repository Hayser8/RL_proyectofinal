'use strict';

// Explanations describe the selected policy's evidence, not invented feature attribution.
(function (root) {
  function playbackPlan(value) {
    if (value === '200') return {steps: 200, delay: 1200, guided: false};
    return {steps: 1, delay: value === '8' ? 15000 : 8000, guided: true};
  }

  function describe(decision, policy) {
    const rows = decision.candidates || [];
    const eligible = rows.filter(c => c.eligible);
    const organic = rows.find(c => c.action === 0);
    const ranking = [...eligible].sort((a, b) => (policy === 'greedy' ? b.estimated_conversion - a.estimated_conversion : b.score - a.score) || a.action - b.action);
    const comparison = [organic, ...ranking.filter(c => c.action !== 0).slice(0, 2)].filter(Boolean);
    const segment = decision.guidance?.segment || 'la categoría de esta visita';
    let reason;
    if (decision.guidance?.converted_before) reason = 'Esta persona ya compró. Mantiene el producto orgánico porque otra compra no añade recompensa.';
    else if (policy === 'organic') reason = 'Esta referencia conserva todos los productos orgánicos; no coloca anuncios.';
    else if (decision.coverage_exploration) reason = 'Asegura la primera impresión de este anuncio apto de la misma PLP. Después de cubrir los 16, prioriza el valor de conversión y recupera marcas atrasadas.';
    else if (decision.forced_pacing) reason = 'La marca elegida está atrasada en su entrega. El controlador prioriza una de sus opciones permitidas para recuperar el ritmo.';
    else if (policy === 'safe_rl') reason = decision.action
      ? 'Entre las opciones permitidas, elige la de mayor valor estimado para el resto de la visita, no solo para este producto.'
      : 'Conserva el orgánico: ofrece el mejor valor estimado disponible o no hay un anuncio con evidencia suficiente para superar el filtro.';
    else if (policy === 'greedy') reason = 'Elige la mayor probabilidad estimada de compra inmediata entre las opciones permitidas, sin planificar el resto de la visita.';
    else if (policy === 'quality') reason = 'Busca un producto de calidad de la misma categoría. Conserva orgánico si ya no quedan opciones que cumplan.';
    else if (policy === 'bid') reason = 'Prioriza el CPC más alto entre los anuncios permitidos. Esta referencia no optimiza la conversión.';
    else if (policy === 'random') reason = 'Elige aleatoriamente entre las opciones permitidas. Sirve para comparar con una política sin aprendizaje.';
    else if (policy === 'relevance') reason = 'Prioriza coincidencia de categoría y reseñas. Esta referencia no usa la planificación aprendida.';
    else reason = decision.reason || 'Selecciona una opción permitida por la política activa.';
    let outcome = decision.purchase
      ? decision.reward ? 'Hubo una primera compra: recompensa 1.' : 'Hubo una compra adicional: recompensa 0.'
      : decision.clicked ? 'Hubo un clic, pero no hubo compra: recompensa 0.' : 'Sin clic ni compra: recompensa 0.';
    outcome += decision.cost_cents ? ' Se cobra el CPC de este anuncio.' : ' No se cobra publicidad en este evento.';
    return {
      context: `La visita busca ${segment}. El espacio ${decision.position} admite un anuncio o puede conservar su producto orgánico.`,
      reason, outcome, eligible: eligible.length, blocked: rows.length - eligible.length,
      comparison,
      filter: decision.guidance?.converted_before ? 'La visita ya compró: se conserva orgánico para no premiar anuncios sin una nueva primera compra.' : ['safe_rl', 'greedy'].includes(policy)
        ? 'Descarta anuncios sin saldo, repetidos o fuera de ritmo. Después exige evidencia de compra suficiente frente al orgánico.'
        : 'Aplica saldo, repetición y ritmo de entrega. El criterio de elección depende de la política de referencia.',
      warning: decision.constraint_conflict ? 'Hay inversión pendiente que no puede entregarse con las opciones que superan el filtro.' : ''
    };
  }
  const api = {playbackPlan, describe};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.LabLesson = api;
})(globalThis);
