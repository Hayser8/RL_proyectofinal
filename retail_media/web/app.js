'use strict';

const $ = id => document.getElementById(id);
const ICONS = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  chart: '<path d="M4 3v17h17M8 15l4-5 4 2 5-7"/>',
  layers: '<path d="m12 3 10 5-10 5L2 8l10-5ZM2 12l10 5 10-5M2 16l10 5 10-5"/>',
  flask: '<path d="M9 3h6M10 3v7L4 19a1 1 0 0 0 1 2h14a1 1 0 0 0 1-2l-6-9V3M7 15h10"/>',
  alert: '<path d="m12 3 10 18H2L12 3ZM12 9v5m0 3v1"/>',
  play: '<path d="m8 4 12 8L8 20V4Z"/>',
  pause: '<path d="M8 4v16M16 4v16"/>',
  step: '<path d="m4 4 11 8-11 8V4ZM20 4v16"/>',
  refresh: '<path d="M20 10a8 8 0 1 0-1 8M20 4v6h-6"/>',
  arrow: '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  spark: '<path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z"/>',
  shield: '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6l8-3Zm-4 9 3 3 5-6"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  scroll: '<path d="M8 4h8a3 3 0 0 1 3 3v10a5 5 0 0 1-5 5h-4a5 5 0 0 1-5-5V7a3 3 0 0 1 3-3Zm4 3v5m-2-2 2 2 2-2"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'
};
const icon = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ICONS.grid}</svg>`;
document.querySelectorAll('[data-icon]').forEach(node => { node.innerHTML = icon(node.dataset.icon); });
const LABELS = {safe_rl: 'Agente entrenado', greedy: 'Compra inmediata', quality: 'Relevancia + calidad', relevance: 'Relevancia y reseñas', bid: 'Puja más alta', random: 'Aleatorio', organic: 'Solo orgánico'};
const SPOTS = [3, 4, 5, 6, 11, 12, 13, 14];
const BRANDS = ['Nova', 'Casa', 'Pulse'];
const CPC = [120, 100, 80];
const TITLES = {simulation: ['Simulación', ''], results: ['Resultados', ''], model: ['Modelo', '']};
const fmt = new Intl.NumberFormat('es-GT');
const dollars = new Intl.NumberFormat('en-US', {style: 'currency', currency: 'USD', minimumFractionDigits: 2});
const number = value => typeof value === 'number' && Number.isFinite(value);
const pct = value => number(value) ? `${(value * 100).toFixed(2)}%` : '—';
const pp = value => number(value) ? `${value >= 0 ? '+' : '−'}${Math.abs(value * 100).toFixed(2)} pp` : '—';
const money = value => number(value) ? dollars.format(value / 100) : '—';
const sum = values => (values || []).reduce((total, value) => total + (number(value) ? value : 0), 0);
const state = {id: null, snapshot: null, activeConfig: null, playing: false, busy: false, resetting: false, timer: null, report: null, competition: null, view: 'simulation', selected: null, generation: 0, modelAvailable: false, catalogueImages: null, lesson: null};

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

async function api(path, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000);
  try {
    const response = await fetch(path, {...options, signal: controller.signal, headers: {'Content-Type': 'application/json', ...(options.headers || {})}});
    if (response.status === 204) return null;
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo completar la solicitud.');
    return data;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('El motor tardó demasiado. Pausa y vuelve a intentarlo.');
    if (error instanceof TypeError) throw new Error('No se pudo conectar con Python. Inicia el laboratorio con «python3 -m retail_media lab».');
    throw error;
  } finally { clearTimeout(timeout); }
}

function showError(message) {
  pause();
  $('error-text').textContent = message;
  $('error-banner').hidden = false;
  $('connection-status').textContent = 'Revisar conexión';
}

function clearError() { $('error-banner').hidden = true; }

function controls() {
  const disabled = state.busy || state.resetting || !state.id || state.snapshot?.done;
  for (const id of ['play-button', 'step-button', 'block-button', 'continue-scroll']) $(id).disabled = Boolean(disabled);
  $('reset-button').disabled = state.busy || state.resetting;
  $('download-button').disabled = !state.snapshot;
  for (const id of ['policy', 'scenario', 'seed', 'session-count', 'budget-scale']) $(id).disabled = state.busy || state.resetting || state.playing;
  $('play-label').textContent = state.playing ? 'Pausar automático' : 'Automático';
  const phase = state.lesson?.phase;
  $('step-label').textContent = state.busy ? 'Preparando…' : !state.lesson ? 'Comenzar recorrido' : phase === 0 ? 'Ver opciones' : phase === 1 ? 'Ver decisión' : 'Siguiente decisión';
  $('lesson-status').textContent = state.playing
    ? LabLesson.playbackPlan($('speed').value).guided ? `Automático: ${LabLesson.playbackPlan($('speed').value).delay / 1000} segundos por etapa. Puedes pausar.` : 'Resumen rápido: se agrupan 200 decisiones por avance.'
    : state.snapshot?.done ? 'Recorrido terminado. Puedes revisar los resultados.' : 'Pausada. Tú decides cuándo continuar.';
  for (const button of document.querySelectorAll('[data-phase]')) button.disabled = state.busy || state.resetting || !state.lesson || Number(button.dataset.phase) > state.lesson.reached;
  $('play-button').querySelector('[data-icon]').innerHTML = icon(state.playing ? 'pause' : 'play');
  // Pause must always remain available while a request is in flight.
  if (state.playing && !state.resetting) $('play-button').disabled = false;
}

function pause() {
  state.playing = false;
  clearTimeout(state.timer);
  state.timer = null;
  controls();
}

function restoreControlFocus(control) {
  if (control instanceof HTMLButtonElement && control.isConnected && !control.disabled &&
      control.getClientRects().length && document.activeElement === document.body && !state.playing) {
    control.focus({preventScroll: true});
  }
}

async function advance(steps = 1, guided = false) {
  if (state.busy || state.resetting || !state.id || state.snapshot?.done) return;
  if (state.lesson && !state.lesson.revealed) revealLesson();
  const generation = state.generation;
  const focusedControl = document.activeElement;
  state.busy = true;
  clearError();
  controls();
  try {
    const snapshot = await api(`/api/simulations/${state.id}/advance`, {method: 'POST', body: JSON.stringify({steps})});
    if (generation !== state.generation) return;
    state.selected = null;
    if (guided && snapshot.last_decision) {
      state.lesson = {snapshot, phase: 0, reached: 0, revealed: false};
      renderLesson();
      renderGrid(state.snapshot);
    } else {
      state.lesson = null;
      state.snapshot = snapshot;
      render(snapshot);
    }
    if (state.snapshot.done) {
      pause();
      $('announcer').textContent = `Simulación finalizada: ${fmt.format(state.snapshot.metrics.sessions_completed)} sesiones, CVR ${pct(state.snapshot.metrics.session_cvr)}.`;
    } else if (!state.playing) {
      const decision = state.snapshot.last_decision;
      if (guided) $('announcer').textContent = $('lesson-heading').textContent + '. ' + $('lesson-body').textContent;
      else $('announcer').textContent = decision ? `Espacio ${decision.position}: ${decision.product_name}. ${decision.reason}` : 'Simulación avanzada.';
    }
  } catch (error) { showError(error.message); }
  finally {
    state.busy = false;
    controls();
    restoreControlFocus(focusedControl);

  }
}

function revealLesson() {
  if (!state.lesson) return;
  state.lesson.phase = 2;
  state.lesson.reached = 2;
  state.lesson.revealed = true;
  state.snapshot = state.lesson.snapshot;
  render(state.snapshot);
  if (state.snapshot.done) pause();
}

async function lessonStep() {
  if (state.busy || state.resetting || !state.id || state.snapshot?.done) return;
  if (state.lesson && state.lesson.phase < 2) {
    state.lesson.phase += 1;
    state.lesson.reached = Math.max(state.lesson.reached, state.lesson.phase);
    if (state.lesson.phase === 2 && !state.lesson.revealed) revealLesson();
    else renderLesson();
    controls();
    $('announcer').textContent = $('lesson-heading').textContent + '. ' + $('lesson-body').textContent;
  } else await advance(1, true);
}

async function playbackTick() {
  clearTimeout(state.timer);
  state.timer = null;
  if (!state.playing) return;
  const plan = LabLesson.playbackPlan($('speed').value);
  if (plan.guided) await lessonStep();
  else await advance(plan.steps);
  if (state.playing && !state.snapshot?.done) state.timer = setTimeout(playbackTick, plan.delay);
}

function renderLesson() {
  const lesson = state.lesson;
  $('lesson-stages').hidden = !lesson;
  $('lesson-body').hidden = !lesson;
  $('lesson-intro').hidden = Boolean(lesson);
  $('continue-scroll').textContent = !lesson ? 'Comenzar recorrido' : lesson.phase === 0 ? 'Ver opciones' : lesson.phase === 1 ? 'Ver decisión' : 'Siguiente decisión';
  $('lesson-location').textContent = lesson ? `Visita ${lesson.snapshot.last_decision.session} · Espacio ${lesson.snapshot.last_decision.position}` : '';
  if (!lesson) {
    $('lesson-heading').textContent = 'Sigamos una decisión';
    $('lesson-body').replaceChildren();
    return;
  }
  const decision = lesson.snapshot.last_decision;
  const explanation = LabLesson.describe(decision, lesson.snapshot.policy);
  const headings = ['¿Qué está evaluando?', '¿Qué opciones puede mostrar?', '¿Qué eligió y qué ocurrió?'];
  $('lesson-heading').textContent = headings[lesson.phase];
  document.querySelectorAll('[data-phase]').forEach(button => {
    const active = Number(button.dataset.phase) === lesson.phase;
    button.classList.toggle('active', active);
    if (active) button.setAttribute('aria-current', 'step'); else button.removeAttribute('aria-current');
  });
  const body = document.createDocumentFragment();
  if (lesson.phase === 0) {
    body.append(element('p', '', explanation.context));
    body.append(element('p', 'lesson-support', decision.guidance?.converted_before ? 'Esta visita ya registró una compra. No puede sumar más recompensa.' : 'Busca una primera compra sin gastar más saldo del disponible. La inversión de cada marca se controla por separado.'));
  } else if (lesson.phase === 1) {
    body.append(element('p', '', explanation.filter));
    body.append(element('p', 'lesson-support', `${explanation.eligible} opciones permitidas · ${explanation.blocked} descartadas. El producto orgánico también cuenta como opción.`));
    const table = element('table', 'lesson-comparison');
    const caption = element('caption', '', `Muestra de ${explanation.comparison.length} de ${explanation.eligible} opciones permitidas, incluido orgánico`);
    table.append(caption);
    const head = element('thead'), row = element('tr');
    for (const text of ['Opción', 'Compra en la visita (est.)']) { const th = element('th', '', text); th.scope = 'col'; row.append(th); }
    head.append(row); table.append(head);
    const rows = element('tbody');
    for (const candidate of explanation.comparison) {
      const tr = element('tr'); tr.append(element('td', '', candidate.name), element('td', '', pct(candidate.score))); rows.append(tr);
    }
    table.append(rows); body.append(table);
    body.append(element('p', 'lesson-support', 'Probabilidad estimada de una primera compra en lo que queda de visita, considerando este producto y los siguientes. Es una predicción del modelo, no un cobro ni una compra garantizada.'));
  } else {
    body.append(element('h3', '', decision.action ? decision.product_name : 'Conserva el producto orgánico'));
    body.append(element('p', '', explanation.reason));
    const chosen = decision.candidates?.find(c => c.action === decision.action);
    const organic = decision.candidates?.find(c => c.action === 0);
    if (lesson.snapshot.policy === 'safe_rl' && !decision.guidance?.converted_before && number(chosen?.score) && number(organic?.score)) body.append(element('p', 'lesson-support', `Primera compra en el resto de visita (estimada): ${pct(chosen.score)}; conservar orgánico: ${pct(organic.score)}.`));
    body.append(element('p', 'lesson-result', explanation.outcome));
    if (decision.cost_cents) body.append(element('p', 'lesson-support', `Cobro observado: ${money(decision.cost_cents)}.`));
    if (explanation.warning) body.append(element('p', 'lesson-warning', explanation.warning));
    if (decision.session !== lesson.snapshot.current?.session || decision.block !== lesson.snapshot.current?.block) body.append(element('p', 'lesson-support', 'La visita o el bloque terminó; el catálogo ya muestra el siguiente. Esta explicación conserva la decisión anterior.'));
  }
  $('lesson-body').replaceChildren(body);
}

async function newSimulation(event) {
  event?.preventDefault();
  if (state.busy || state.resetting) return;
  if (!$('experiment-form').reportValidity()) return;
  const focusedControl = document.activeElement;
  pause();
  state.resetting = true;
  $('product-grid').setAttribute('aria-busy', 'true');
  state.generation += 1;
  state.lesson = null;
  clearError();
  controls();
  try {
    if (state.id) {
      await api(`/api/simulations/${state.id}`, {method: 'DELETE'}).catch(() => null);
      state.id = null;
    }
    const configuration = {
      policy: $('policy').value, scenario: $('scenario').value, seed: Number($('seed').value),
      sessions: Number($('session-count').value), budget_scale: Number($('budget-scale').value)
    };
    const snapshot = await api('/api/simulations', {method: 'POST', body: JSON.stringify(configuration)});
    state.activeConfig = configuration;
    if (state.report && state.report.model_id !== snapshot.model?.id) {
      state.report = null;
      await loadEvaluation();
    }
    state.id = snapshot.id;
    state.snapshot = snapshot;
    state.selected = null;
    render(snapshot);
    $('product-scroll').scrollTop = 0;
    $('connection-status').textContent = 'Motor Python conectado';
    $('reset-button').lastChild.textContent = 'Reiniciar';
    $('settings').open = false;
    $('decision-details').open = false;
    $('announcer').textContent = 'Nueva simulación lista. Pulsa Comenzar recorrido para avanzar a tu ritmo.';
  } catch (error) { showError(error.message); }
  finally { state.resetting = false; $('product-grid').setAttribute('aria-busy', 'false'); controls(); restoreControlFocus(focusedControl); }
}

function render(snapshot) {
  const m = snapshot.metrics || {};
  $('metric-cvr').textContent = pct(m.session_cvr);
  $('metric-organic').textContent = pct(m.organic_session_cvr);
  $('metric-delta').textContent = pp(m.delta_cvr);
  $('metric-delta').className = number(m.delta_cvr) ? (m.delta_cvr >= 0 ? 'positive' : 'negative') : '';
  $('metric-cvr-note').textContent = m.sessions_completed ? `${fmt.format(m.converted_sessions)} con compra / ${fmt.format(m.sessions_completed)} sesiones cerradas` : 'Se calcula al cerrar sesiones';
  $('metric-delta-note').textContent = m.sessions_completed ? 'En vivo · sin intervalo' : 'Sin sesiones cerradas';
  $('metric-spend').textContent = money(sum(m.spend_cents));
  $('metric-spend-note').textContent = `Presupuesto ${money(sum(m.budget_cents))}`;
  $('simulation-progress').value = snapshot.progress || 0;
  $('traffic-note').hidden = !(m.sessions_target < snapshot.requested_sessions);
  $('traffic-note').textContent = `Tráfico al 22%. Se mantiene el presupuesto asignado.`;
  $('progress-label').textContent = `${fmt.format(m.sessions_completed || 0)} / ${fmt.format(m.sessions_target || snapshot.requested_sessions || 0)} sesiones`;
  $('active-policy').textContent = LABELS[snapshot.policy] || snapshot.policy;
  renderGrid(snapshot);
  renderDecision(snapshot.last_decision);
  renderBrands(m);
  renderEvents(snapshot.events || []);
  renderLesson();
  const conflicts = m.constraint_conflicts || 0;
  $('budget-conflicts').textContent = conflicts ? `${fmt.format(conflicts)} conflictos` : '';
  $('budget-conflicts').hidden = !conflicts;
  $('budget-conflicts').classList.toggle('negative', Boolean(conflicts));
  $('completion-banner').hidden = !snapshot.done;
  if (snapshot.done) $('completion-text').textContent = `CVR ${pct(m.session_cvr)}; cambio ${pp(m.delta_cvr)} frente a orgánico. Entrega ${pct(sum(m.delivery) / Math.max(1, (m.delivery || []).length))}. ${conflicts ? 'Hay inversión pendiente por restricciones.' : ''}`;
}

function renderGrid(snapshot) {
  const current = snapshot.current;
  if (!current?.products) return;
  const explaining = state.lesson && !state.lesson.revealed;
  const last = explaining ? state.lesson.snapshot.last_decision : snapshot.last_decision;
  const sameBlock = last && last.session === current.session && last.block === current.block;
  const active = sameBlock ? last.position : null;
  $('session-context').textContent = `Sesión ${current.session} · Bloque ${current.block}`;
  $('intent-badge').textContent = current.segment || 'Sesión terminada';
  const focused = document.activeElement?.dataset?.position;
  const map = document.createDocumentFragment();
  for (let p = 1; p <= 20; p++) {
    const cell = element('span', 'slot-cell', p);
    cell.classList.toggle('eligible', SPOTS.includes(p));
    cell.classList.toggle('current', p === active);
    cell.title = `Espacio ${p}${SPOTS.includes(p) ? ': admite patrocinados' : ': orgánico'}`;
    map.append(cell);
  }
  $('slot-overview').replaceChildren(map);
  const grid = document.createDocumentFragment();
  for (const product of current.products) {
    const button = element('button', `product ${product.status || ''}`);
    button.type = 'button';
    button.dataset.position = product.position;
    button.classList.toggle('sponsored', Boolean(product.sponsored));
    button.classList.toggle('is-current', !explaining && sameBlock && product.position === last.position);
    button.classList.toggle('is-evaluating', explaining && sameBlock && product.position === last.position);
    button.classList.toggle('not-viewed', product.status === 'not_viewed');
    const top = element('span', 'product-topline');
    const label = !product.observed ? (product.status === 'not_viewed' ? 'No visto' : SPOTS.includes(product.position) ? 'Por decidir' : 'Orgánico') : product.sponsored ? 'Patrocinado' : 'Orgánico';
    top.append(element('span', '', `#${product.position}`), element('span', 'product-label', product.sponsored ? 'Patrocinado' : ''));
    const source = LabCatalogImages.describe(product.image_key, state.catalogueImages);
    let image;
    if (source) {
      const ns = 'http://www.w3.org/2000/svg';
      image = document.createElementNS(ns, 'svg');
      image.setAttribute('class', 'product-image');
      const box = source.rect;
      image.setAttribute('viewBox', `${box.left} ${box.top} ${box.width} ${box.height}`);
      image.setAttribute('preserveAspectRatio', 'xMidYMid meet');
      const definitions = document.createElementNS(ns, 'defs');
      const clip = document.createElementNS(ns, 'clipPath');
      const clipId = `catalogue-photo-${product.position}`;
      clip.setAttribute('id', clipId);
      const frame = document.createElementNS(ns, 'rect');
      for (const [attribute, value] of Object.entries({x: box.left, y: box.top, width: box.width, height: box.height})) frame.setAttribute(attribute, value);
      clip.append(frame); definitions.append(clip);
      const photo = document.createElementNS(ns, 'image');
      photo.setAttribute('href', source.url);
      photo.setAttribute('width', source.width); photo.setAttribute('height', source.height);
      photo.setAttribute('clip-path', `url(#${clipId})`);
      image.append(definitions, photo);
    } else image = element('span', 'product-image image-unavailable', 'Sin imagen');
    image.setAttribute('aria-hidden', 'true');
    const title = product.name?.replace(/^(Nova|Casa|Pulse)\s+/, '') || product.name || 'Producto';
    const name = element('span', 'product-name', title);
    const brand = element('span', 'product-brand', product.brand || product.category);
    const bottom = element('span', 'product-bottom');
    bottom.append(element('span', 'product-price', money(product.price_cents)));
    if (product.purchase || product.clicked) {
      const event = element('span', 'product-event', product.purchase ? 'Compra' : 'Clic');
      bottom.append(event);
    }
    button.setAttribute('aria-label', `Espacio ${product.position}, ${title}, ${label}, ${money(product.price_cents)}${product.purchase ? ', compra observada' : product.clicked ? ', clic observado' : ''}`);
    button.append(top, image, name);
    if (product.sponsored && product.brand) button.append(brand);
    button.append(bottom);
    button.addEventListener('click', () => inspectProduct(product, current, last));
    grid.append(button);
  }
  $('product-grid').replaceChildren(grid);
  // Keep the current choice in view without scrolling the whole page.
  const chosen = $('product-grid').querySelector('.is-current, .is-evaluating');
  if (chosen) {
    const bounds = chosen.getBoundingClientRect(), viewport = $('product-scroll').getBoundingClientRect();
    if (bounds.top < viewport.top || bounds.bottom > viewport.bottom) {
      $('product-scroll').scrollTop += bounds.top - viewport.top - 8;
    }
  }
  if (focused) $('product-grid').querySelector(`[data-position="${Number(focused)}"]`)?.focus({preventScroll: true});
  const observed = current.products.filter(p => p.observed).length;
  $('grid-caption').textContent = `${observed} / 20 vistos`;
  $('observed-label').textContent = `Próximo espacio: ${current.position || 'fin'}`;
}

function inspectProduct(product, current, decision) {
  pause();
  if (state.lesson && !state.lesson.revealed && product.position === state.lesson.snapshot.last_decision.position && current.session === state.lesson.snapshot.last_decision.session && current.block === state.lesson.snapshot.last_decision.block) {
    $('lesson-heading').scrollIntoView({block: 'nearest'});
    return;
  }
  $('decision-details').open = true;
  $('decision-summary').textContent = `Espacio ${product.position}`;
  if (decision && product.position === decision.position && current.session === decision.session && current.block === decision.block) {
    renderDecision(decision);
  } else {
    $('decision-empty').hidden = true;
    $('decision-content').hidden = false;
    $('decision-position').textContent = `Espacio ${product.position}`;
    $('decision-policy').textContent = product.sponsored ? 'Patrocinado' : 'Orgánico';
    $('decision-product').textContent = product.name;
    $('decision-reason').textContent = !product.observed ? 'Este espacio aún no se ha visto.' : product.sponsored ? 'Producto patrocinado. Se muestran sus eventos observados.' : 'Producto orgánico.';
    $('decision-reward').textContent = '—';
    $('decision-cost').textContent = product.observed ? money(product.cost_cents || 0) : '—';
    $('decision-tags').replaceChildren(element('span', '', product.observed ? 'Evento observado' : 'Sin observación'));
    $('candidate-list').replaceChildren(element('p', 'empty-copy', 'Los candidatos están disponibles en la última decisión.'));
    $('conflict-note').hidden = true;
  }
  $('decision-details').scrollIntoView({block: 'nearest', behavior: 'instant'});
}

function renderDecision(decision) {
  $('decision-empty').hidden = Boolean(decision);
  $('decision-content').hidden = !decision;
  $('decision-summary').textContent = decision ? `Espacio ${decision.position} · ${decision.action ? 'Patrocinado' : 'Orgánico'}` : 'Sin decisiones';
  if (!decision) return;
  $('decision-position').textContent = `Espacio ${decision.position} · Sesión ${decision.session}`;
  $('decision-policy').textContent = LABELS[state.snapshot?.policy] || '';
  $('decision-product').textContent = decision.product_name || 'Conservar orgánico';
  $('decision-reason').textContent = decision.reason || 'Decisión basada en el modelo aprendido y las restricciones disponibles.';
  $('decision-reward').textContent = number(decision.reward) ? String(decision.reward) : '—';
  $('decision-cost').textContent = money(decision.cost_cents || 0);
  const tags = document.createDocumentFragment();
  tags.append(element('span', '', decision.action ? 'Patrocinado' : 'Orgánico'));
  tags.append(element('span', decision.clicked && !decision.purchase ? 'warning-tag' : '', decision.purchase ? (decision.reward ? 'Primera compra' : 'Compra sin recompensa adicional') : decision.clicked ? 'Clic sin compra' : 'Sin clic'));
  if (decision.forced_pacing) tags.append(element('span', 'warning-tag', 'Intervención de pacing'));
  if (decision.constraint_conflict) tags.append(element('span', 'warning-tag', 'Conflicto registrado'));
  $('decision-tags').replaceChildren(tags);
  $('conflict-note').hidden = !decision.constraint_conflict;
  const candidates = [...(decision.candidates || [])].sort((a, b) => Number(b.action === decision.action) - Number(a.action === decision.action) || Number(b.eligible) - Number(a.eligible) || (b.score || 0) - (a.score || 0));
  const rows = document.createDocumentFragment();
  for (const candidate of candidates) {
    const row = element('div', `candidate-row${candidate.action === decision.action ? ' chosen' : ''}${candidate.eligible === false ? ' blocked' : ''}`);
    const heading = element('div', 'candidate-head');
    heading.append(element('strong', '', candidate.name || (candidate.action ? `Producto ${candidate.action}` : 'Orgánico')),
      element('span', 'candidate-score', number(candidate.score) ? candidate.score.toFixed(3) : '—'));
    row.append(heading, element('p', '', candidate.reason || (candidate.eligible ? 'Candidato disponible' : 'Excluido por restricciones')));
    rows.append(row);
  }
  $('candidate-list').replaceChildren(rows);
  if (!candidates.length) $('candidate-list').append(element('p', 'empty-copy', 'Esta política de referencia no usa estimaciones de valor.'));
}

function renderBrands(m) {
  const fragment = document.createDocumentFragment();
  for (let b = 0; b < 3; b++) {
    const item = element('article', 'brand-entry');
    const header = element('div', 'brand-entry-header');
    const brand = element('span', 'brand-name');
    brand.append(element('span', `brand-mark brand-${b}`, BRANDS[b][0]), element('strong', '', BRANDS[b]));
    const delivered = m.delivery?.[b];
    header.append(brand, element('span', '', number(delivered) ? pct(delivered) : '—'));
    const track = element('div', 'budget-track');
    const bar = element('span');
    bar.style.width = `${Math.min(100, Math.max(0, (delivered || 0) * 100))}%`;
    track.append(bar);
    const facts = element('div', 'brand-facts');
    facts.append(element('span', '', `${money(m.spend_cents?.[b] || 0)} / ${money(m.budget_cents?.[b])}`),
      element('strong', '', `${fmt.format(m.brand_impressions?.[b] || 0)} impresiones`));
    item.append(header, track, facts, element('p', 'brand-small', `CPC ${money(CPC[b])} · Saldo ${money(m.remaining_cents?.[b] ?? m.budget_cents?.[b])}`));
    fragment.append(item);
  }
  $('brand-ledger').replaceChildren(fragment);
}

function renderEvents(events) {
  const recent = events.filter(event => event.kind === 'click' || event.kind === 'purchase').slice(-8);
  if (!recent.length) { $('event-log').replaceChildren(element('p', 'empty-copy', 'Sin clics ni compras.')); return; }
  const fragment = document.createDocumentFragment();
  for (const event of recent.reverse()) {
    const row = element('div', 'event-row');
    const first = element('span', 'event-position', `#${event.position || '—'}`);
    const text = element('div', 'event-text');
    text.append(element('strong', '', event.text || event.message || event.description || event.kind || 'Evento observado'), element('span', '', `Sesión ${event.session || '—'} · ${event.brand || 'Simulación'}`));
    row.append(first, text, element('span', 'event-money', number(event.cost_cents) ? money(event.cost_cents) : ''));
    fragment.append(row);
  }
  $('event-log').replaceChildren(fragment);
}

function showView(view, updateHash = true) {
  if (!TITLES[view]) view = 'simulation';
  state.view = view;
  if (view !== 'simulation') pause();
  for (const id of ['simulation', 'results', 'model']) $(`${id}-view`).hidden = id !== view;
  document.querySelectorAll('[data-view]').forEach(button => {
    button.classList.toggle('active', button.dataset.view === view);
    if (button.dataset.view === view) button.setAttribute('aria-current', 'page');
    else button.removeAttribute('aria-current');
  });
  $('page-title').textContent = TITLES[view][0];
  $('page-description').textContent = TITLES[view][1];
  $('page-description').hidden = !TITLES[view][1];
  if (updateHash) history.replaceState(null, '', `#${view}`);
  if (updateHash) window.scrollTo({top: 0, behavior: 'instant'});
  if (view === 'results' || view === 'model') loadEvaluation();
}

function clearEvaluation(message) {
  state.report = null;
  $('evaluation-status').textContent = message;
  $('checks-count').textContent = 'Sin evidencia compatible cargada';
  $('evaluation-highlights').hidden = true;
  for (const id of ['evaluation-highlights', 'evaluation-table', 'comparison-chart', 'evaluation-conclusion', 'integrity-checks', 'training-chart', 'seed-splits']) $(id).replaceChildren();
  $('training-count').textContent = '—';
  $('evaluation-sample').textContent = '';
  $('training-summary').textContent = message;
}

let competitionLoading = false;
async function loadCompetition() {
  if (competitionLoading) return;
  competitionLoading = true;
  $('competition-retry').hidden = true;
  $('competition-status').textContent = 'Cargando impresiones…';
  try {
    const data = await api('/api/competition');
    if (data.status !== 'ready') throw new Error(data.message || 'No hay un informe de impresiones compatible.');
    state.competition = data.report;
    renderCompetition();
  } catch (error) {
    state.competition = null;
    renderAssessment();
    $('competition-status').textContent = error.message;
    $('competition-content').hidden = true;
    $('competition-sample').textContent = '';
    for (const id of ['competition-chart', 'competition-bars', 'competition-table', 'competition-legend']) $(id).replaceChildren();
    $('competition-retry').hidden = false;
  } finally { competitionLoading = false; }
}

function renderCompetition() {
  const report = state.competition;
  renderAssessment();
  if (!report) return;
  const currentModel = state.snapshot?.model?.id || state.report?.model_id;
  if (currentModel && report.model_id !== currentModel) {
    $('competition-content').hidden = true;
    $('competition-sample').textContent = '';
    $('competition-status').textContent = 'El informe de impresiones pertenece a otro modelo. Regénéralo antes de compararlo.';
    return;
  }
  const plp = report.scenarios?.[$('evaluation-scenario').value]?.plps?.[Number($('competition-plp').value)];
  const mode = $('competition-scale').value;
  const groups = LabClusters.summarize(plp, mode);
  $('competition-content').hidden = groups.length !== 2;
  $('competition-status').textContent = groups.length === 2 ? '' : 'No hay datos compatibles para comparar estos clusters. Regenera el informe de impresiones.';
  $('competition-sample').textContent = plp ? `${fmt.format(plp.visits)} visitas a esta PLP · Semilla ${report.seed} · Réplica descriptiva` : '';
  if (groups.length !== 2) return;
  const compact = new Intl.NumberFormat('es-GT', {maximumFractionDigits: 1});
  const legend = document.createDocumentFragment();
  for (const group of groups) {
    const item = element('div');
    item.append(element('h3', '', `${group.label} · ${group.count} anuncios`),
      element('strong', '', `${fmt.format(group.total)} impresiones · ${pct(group.share)}`),
      element('p', '', `${compact.format(group.perAd)} por anuncio del cluster`));
    legend.append(item);
  }
  $('competition-legend').replaceChildren(legend);
  const coverage = plp.coverage;
  $('competition-coverage').textContent = coverage.complete
    ? `Cobertura ${coverage.served}/${coverage.target}: todos tienen impresiones. Mínimo observado: ${fmt.format(coverage.minimum)} por anuncio.`
    : `Cobertura ${coverage.served}/${coverage.target}: ${coverage.pending.length} anuncios pendientes. No hay exposición inventada para completar el mínimo.`;
  $('competition-chart-label').textContent = mode === 'mean' ? 'Impresiones acumuladas · promedio por anuncio' : 'Impresiones acumuladas · total por cluster';
  const width = Math.max(260, $('competition-chart').clientWidth || 700), height = 230;
  const left = 40, right = width - 16, top = 16, bottom = 184;
  const maxY = Math.max(1, ...groups.flatMap(g => g.values.map(p => p.value)));
  const x = v => left + v / Math.max(1, plp.visits) * (right - left);
  const y = v => bottom - v / maxY * (bottom - top);
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `Impresiones acumuladas en la PLP ${plp.category}, ${mode === 'mean' ? 'promedio por anuncio' : 'total por cluster'}. ${groups.map(g => `${g.label}: ${compact.format(mode === 'mean' ? g.perAd : g.total)}`).join('; ')}. Eje horizontal: visitas finalizadas. Eje vertical: impresiones.`);
  const add = (tag, attrs, text) => {
    const node = document.createElementNS(ns, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    if (text !== undefined) node.textContent = text;
    svg.append(node); return node;
  };
  for (const value of [...new Set([0, Math.round(maxY / 2), maxY])]) {
    add('line', {x1:left, x2:right, y1:y(value), y2:y(value), stroke:'var(--line)'});
    add('text', {x:left - 10, y:y(value) + 4, 'text-anchor':'end'}, compact.format(value));
  }
  for (const value of [...new Set([0, Math.round(plp.visits / 2), plp.visits])]) {
    add('text', {x:x(value), y:206, 'text-anchor':value === 0 ? 'start' : value === plp.visits ? 'end' : 'middle'}, fmt.format(value));
  }
  add('text', {x:(left + right) / 2, y:228, 'text-anchor':'middle'}, 'Visitas finalizadas a esta PLP');
  for (const group of groups) {
    const color = group.key === 'winners' ? 'var(--blue)' : 'var(--ink)';
    const path = group.values.map((p, i) => `${i ? 'L' : 'M'}${x(p.visits).toFixed(2)},${y(p.value).toFixed(2)}`).join(' ');
    add('path', {d:path, fill:'none', stroke:color, 'stroke-width':2.5, ...(group.key === 'others' ? {'stroke-dasharray':'7 5'} : {})});
    add('circle', {cx:x(plp.visits), cy:y(mode === 'mean' ? group.perAd : group.total), r:3.5, fill:color});
  }
  $('competition-chart').replaceChildren(svg);
  const winners = groups[0], others = groups[1];
  const winnerValue = mode === 'mean' ? winners.perAd : winners.total;
  const otherValue = mode === 'mean' ? others.perAd : others.total;
  const exposed = plp.ads.filter(a => a.impressions > 0).length;
  $('competition-takeaway').textContent = (winnerValue > otherValue
    ? 'El cluster winner recibe más impresiones en esta réplica. '
    : winnerValue < otherValue ? 'El cluster loser recibe más impresiones en esta réplica. '
    : 'Los clusters reciben las mismas impresiones en esta réplica. ')
    + `${exposed} de ${plp.ads.length} candidatos tuvieron exposición. La mejora de conversión es estimada; el reparto observado también depende de saldo, contexto y ritmo.`;
  const metrics = report.scenarios[$('evaluation-scenario').value].metrics;
  const balance = document.createDocumentFragment();
  balance.append(element('p', 'section-copy', `Misma réplica, todas las PLP: CVR ${pct(metrics.session_cvr)} frente a ${pct(metrics.organic_session_cvr)} orgánico (${pp(metrics.delta_cvr)}). Una sola semilla describe este caso; no demuestra superioridad.`));
  balance.append(element('p', 'section-copy', BRANDS.map((brand, i) => `${brand}: ${money(metrics.spend_cents[i])} de ${money(metrics.budget_cents[i])}`).join(' · ')));
  balance.append(element('p', 'section-copy', `${fmt.format(metrics.pacing_interventions)} recuperaciones de ritmo · ${fmt.format(metrics.constraint_conflicts)} conflictos de entrega y calidad · ${metrics.budget_overshoots} sobregiros.`));
  $('competition-balance').replaceChildren(balance);
  const reference = document.createDocumentFragment();
  for (const group of groups) reference.append(element('p', 'section-copy', `${group.label}: ${group.count} anuncios; mejora media estimada de primera compra en el resto de visita: ${pp(group.mean_reference_lift)} frente a orgánico en el contexto de referencia. Media entre anuncios, no CVR observado.`));
  $('competition-reference').replaceChildren(reference);
  const bars = document.createDocumentFragment(), rows = document.createDocumentFragment();
  const maxCount = Math.max(1, ...plp.ads.map(a => a.impressions));
  for (const ad of [...plp.ads].sort((a, b) => b.impressions - a.impressions || a.action - b.action)) {
    const line = element('div', `chart-row ${ad.cluster === 'winners' ? 'cluster-winner' : 'cluster-other'}`);
    const track = element('div', 'chart-track'), bar = element('div', 'chart-bar');
    bar.style.width = `${ad.impressions / maxCount * 100}%`; track.append(bar);
    line.append(element('span', 'chart-label', ad.name), track, element('strong', '', fmt.format(ad.impressions))); bars.append(line);
    const row = element('tr');
    const exclusions = Object.entries(ad.blocked).filter(([, count]) => count).map(([key, count]) => `${report.block_labels[key] || key}: ${fmt.format(count)}`).join('; ') || 'Ninguna';
    for (const text of [ad.name, ad.cluster === 'winners' ? 'Winner' : 'Loser', fmt.format(ad.impressions), fmt.format(ad.eligible), fmt.format(ad.lost_ranking), fmt.format(ad.lost_pacing), fmt.format(ad.lost_coverage || 0), exclusions]) row.append(element('td', '', text));
    rows.append(row);
  }
  $('competition-bars').replaceChildren(bars);
  $('competition-table').replaceChildren(rows);
  $('competition-table-caption').textContent = `${plp.category}: ${fmt.format(plp.opportunities)} decisiones observadas; ${fmt.format(plp.organic_wins)} conservaron orgánico. Cada anuncio se considera en cada decisión.`;
}

async function loadEvaluation() {
  if (!state.competition) loadCompetition();
  if (state.report) { renderEvaluation(); return; }
  try {
    const data = await api('/api/evaluation');
    if (data.status !== 'ready') {
      clearEvaluation(data.message || 'La evaluación aún no está disponible para este modelo.');
      return;
    }
    state.report = data.report;
    renderEvaluation();
    renderModelEvidence();
  } catch (error) { clearEvaluation(error.message); }
}

function renderEvaluation() {
  const report = state.report;
  if (!report) return;
  const scenario = report.scenarios?.[$('evaluation-scenario').value];
  if (!scenario?.policies) { $('evaluation-status').textContent = 'No hay resultados para este escenario.'; return; }
  $('evaluation-status').textContent = '';
  const policies = scenario.policies;
  const learned = policies.safe_rl;
  const rows = document.createDocumentFragment(), chart = document.createDocumentFragment();
  const maxCvr = Math.max(.01, ...Object.values(policies).map(v => v.session_cvr || 0)) * 1.1;
  for (const key of ['organic', 'bid', 'random', 'relevance', 'quality', 'greedy', 'safe_rl']) {
    if (!policies[key]) continue;
    const metric = policies[key], row = element('tr', key === 'safe_rl' ? 'highlight-row' : '');
    const interval = metric.delta_cvr_ci95;
    for (const value of [LABELS[key], pct(metric.session_cvr), pp(metric.delta_cvr), interval?.map(pp).join(' a ') || 'No disponible', pct(metric.delivery_mean), fmt.format(metric.constraint_conflicts || 0)]) row.append(element('td', '', value));
    rows.append(row);
    const line = element('div', `chart-row ${key === 'safe_rl' ? 'rl' : key}`);
    const track = element('div', 'chart-track'), bar = element('div', 'chart-bar');
    bar.style.width = `${Math.max(0, Math.min(100, metric.session_cvr / maxCvr * 100))}%`;
    track.append(bar);
    line.append(element('span', 'chart-label', LABELS[key]), track, element('strong', '', pct(metric.session_cvr)));
    chart.append(line);
  }
  $('evaluation-table').replaceChildren(rows);
  $('comparison-chart').replaceChildren(chart);
  $('evaluation-sample').textContent = `${fmt.format(learned?.sessions || 0)} sesiones por política · ${report.test?.independent_days || '—'} ejecuciones independientes`;
  const highlights = document.createDocumentFragment();
  for (const [title, value, detail] of [['Conversión del agente', pct(learned?.session_cvr), `Orgánico: ${pct(learned?.organic_session_cvr)}`], ['Cambio frente a orgánico', pp(learned?.delta_cvr), 'Puntos porcentuales'], ['Presupuesto entregado', pct(learned?.delivery_mean), 'Media de las tres marcas']]) {
    const item = element('div'); item.append(element('h3', '', title), element('strong', '', value), element('p', '', detail)); highlights.append(item);
  }
  $('evaluation-highlights').replaceChildren(highlights);
  $('evaluation-highlights').hidden = false;
  const conclusion = document.createDocumentFragment();
  const visitsWithPurchase = (learned.session_cvr * 100).toFixed(1);
  const organicWithPurchase = (learned.organic_session_cvr * 100).toFixed(1);
  conclusion.append(element('p', '', `De cada 100 visitas, unas ${visitsWithPurchase} compran con el agente, frente a ${organicWithPurchase} sin anuncios. ` + (learned?.cvr_empirical_pass ? 'La comparación apoya una mejora frente a orgánico en este escenario.' : 'La incertidumbre de la prueba no permite establecer una mejora frente a orgánico.')));
  conclusion.append(element('p', '', learned?.delivery_empirical_pass
    ? 'Las tres marcas superan el 90% de entrega media. La media no significa que se cumpla en cada ejecución.'
    : 'No todas las marcas alcanzan el 90% de entrega media. Puede quedar saldo pendiente si no hay anuncios aptos para las visitas disponibles.'));
  const comparisons = Object.values(scenario.comparisons || {});
  const demonstrated = comparisons.some(row => row.superiority_demonstrated);
  conclusion.append(element('p', 'comparison-caveat', demonstrated
    ? 'La tabla permite revisar también la diferencia frente a calidad y compra inmediata.'
    : 'El agente no demuestra una ventaja concluyente frente a las referencias de calidad y compra inmediata. Elegir RL no garantiza que sea la mejor alternativa.'));
  $('evaluation-conclusion').replaceChildren(conclusion);
  renderCompetition();
  renderModelEvidence();
}

function renderAssessment() {
  const assessment = state.competition?.assessment;
  const currentModel = state.snapshot?.model?.id || state.report?.model_id;
  if (!assessment?.complete || (currentModel && state.competition.model_id !== currentModel)
      || (state.snapshot?.serving_id && state.competition.serving_id !== state.snapshot.serving_id)) {
    $('model-assessment').textContent = 'Falta una evaluación compatible para completar la valoración técnica.';
    $('assessment-table').replaceChildren();
    return;
  }
  $('model-assessment').textContent = `${assessment.score}/100 para esta entrega; antes ${assessment.before_score}/100. La rúbrica valora representación, aprendizaje, controles, cobertura y explicación. Los datos siguen siendo sintéticos.`;
  const rows = document.createDocumentFragment();
  for (const item of assessment.rows) {
    const row = element('tr');
    for (const value of [item.name, item.before, item.points, item.maximum, item.reason]) row.append(element('td', '', String(value)));
    rows.append(row);
  }
  $('assessment-table').replaceChildren(rows);
}

function renderModelEvidence() {
  renderAssessment();
  const report = state.report;
  if (!report) return;
  const training = report.training || {};
  $('training-count').textContent = fmt.format(training.observations || 0);
  $('training-summary').textContent = `Se aprende con ${fmt.format(training.observations || 0)} transiciones sintéticas. Validación revisa las predicciones; evaluación prueba la política con ${report.test?.independent_days || '—'} semillas nuevas. Estos tres conjuntos tienen funciones distintas.`;
  const curve = training.history || [];
  if (curve.length) {
    const values = curve.map(row => row.brier_score).filter(number), low = Math.min(...values) * .98, high = Math.max(...values) * 1.02;
    const width = Math.max(240, $('training-chart').clientWidth || 900);
    const x = i => 54 + i / Math.max(1, values.length - 1) * (width - 78);
    const y = v => 155 - (v - low) / Math.max(.000001, high - low) * 115;
    const path = values.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ');
    $('training-chart').innerHTML = `<svg viewBox="0 0 ${width} 200" role="img" aria-label="Error Brier de validación durante el aprendizaje; menor es mejor"><line x1="54" y1="155" x2="${width - 24}" y2="155" stroke="var(--line)"/><text x="0" y="42">${high.toFixed(4)}</text><text x="0" y="158">${low.toFixed(4)}</text><path d="${path}" fill="none" stroke="var(--blue)" stroke-width="2.5"/><text x="54" y="188">${Math.round((curve[0]?.observations || 0) / 1000)}k</text><text x="${width - 56}" y="188">${Math.round((training.observations || 0) / 1000)}k</text></svg>`;
  }
  const splits = document.createDocumentFragment();
  for (const [label, detail] of [['Entrenamiento', `Semilla ${training.training_seed ?? '—'}`], ['Validación', `Semilla ${training.validation_seed ?? '—'}`], ['Evaluación', `Semillas ${(report.test?.seeds || []).join(', ')}`]]) {
    const cell = element('div'); cell.append(element('strong', '', label), element('span', '', detail)); splits.append(cell);
  }
  $('seed-splits').replaceChildren(splits);
  const descriptions = {
    click_only: 'Un anuncio puede atraer clics y gastar dinero sin aportar una compra. Ese evento debe valer cero.',
    reward_symmetry: 'La misma primera compra aporta recompensa 1 tanto en posiciones orgánicas como patrocinadas.',
    one_reward: 'Repetir compras o continuar una sesión ya convertida no multiplica la recompensa.',
    budget_zero: 'Las máscaras de acciones impiden elegir campañas que no pueden pagar otro clic.',
    frozen: 'La simulación y el conjunto de test ejecutan inferencia, sin aprender de sus propios resultados.',
    no_future: 'Los indicadores parciales se construyen con sesiones finalizadas, no con eventos precalculados.',
    fallback: 'Sin soporte suficiente en los datos, el filtro conserva orgánico o hace visible un conflicto.'
  };
  const openChecks = new Set([...$('integrity-checks').querySelectorAll('details[open]')].map(d => d.dataset.check));
  const checks = report.integrity_checks || [], fragment = document.createDocumentFragment();
  for (const check of checks) {
    const item = element('details', 'integrity-check');
    item.dataset.check = check.id;
    item.open = openChecks.has(check.id);
    const summary = element('summary');
    summary.append(element('span', '', check.name), element('span', check.passed ? 'positive' : 'negative', check.passed ? 'Pasa' : 'Falla'));
    const content = element('p', '', descriptions[check.id] || check.description || (check.id === 'session_cap' ? 'Se comprueba que la suma de recompensas no supere el número de visitas.' : 'Se inflan las señales monetarias sin añadir compras y se comprueba que la recompensa no aumente.'));
    item.append(summary, content); fragment.append(item);
  }
  $('integrity-checks').replaceChildren(fragment);
  $('checks-count').textContent = `${checks.filter(c => c.passed).length} de ${checks.length} pruebas dirigidas pasan`;
}

function downloadState() {
  if (!state.snapshot) return;
  const exported = {exported_at: new Date().toISOString(), source: 'Retail Media Lab', synthetic: true, configuration: state.activeConfig, snapshot: state.snapshot};
  const blob = new Blob([JSON.stringify(exported, null, 2)], {type: 'application/json'});
  const url = URL.createObjectURL(blob), anchor = document.createElement('a');
  anchor.href = url; anchor.download = `retail-lab-${state.snapshot.policy}-${state.snapshot.seed}.json`;
  document.body.append(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
$('experiment-form').addEventListener('submit', newSimulation);
$('experiment-form').addEventListener('invalid', () => { $('settings').open = true; }, true);
document.addEventListener('click', event => {
  if (!$('settings').contains(event.target)) $('settings').open = false;
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && $('settings').open) {
    $('settings').open = false;
    $('settings').querySelector('summary').focus();
  }
});
$('experiment-form').addEventListener('change', event => { if (event.target.id !== 'speed') $('reset-button').lastChild.textContent = 'Aplicar'; });
$('step-button').addEventListener('click', () => { pause(); lessonStep(); });
$('block-button').addEventListener('click', () => { pause(); advance(8); });
$('continue-scroll').addEventListener('click', () => { pause(); lessonStep(); $('lesson-heading').scrollIntoView({block:'nearest'}); });
$('play-button').addEventListener('click', () => { if (state.playing) pause(); else { state.playing = true; controls(); playbackTick(); } });
document.querySelectorAll('[data-phase]').forEach(button => button.addEventListener('click', () => {
  if (!state.lesson || Number(button.dataset.phase) > state.lesson.reached) return;
  pause(); state.lesson.phase = Number(button.dataset.phase); renderLesson(); controls();
}));
$('speed').addEventListener('change', () => { if (state.playing) pause(); });
document.querySelector('.training-details').addEventListener('toggle', () => { if (document.querySelector('.training-details').open) renderModelEvidence(); });
$('retry-button').addEventListener('click', () => state.catalogueImages && state.modelAvailable ? newSimulation() : initialize());
$('download-button').addEventListener('click', downloadState);
$('go-results').addEventListener('click', () => { showView('results'); $('page-title').scrollIntoView(); });
$('evaluation-scenario').addEventListener('change', renderEvaluation);
$('competition-plp').addEventListener('change', renderCompetition);
$('competition-scale').addEventListener('change', renderCompetition);
$('competition-retry').addEventListener('click', loadCompetition);
window.addEventListener('hashchange', () => showView(location.hash.slice(1), false));
let resizePending = false;
window.addEventListener('resize', () => {
  if (resizePending || !['model', 'results'].includes(state.view)) return;
  resizePending = true;
  requestAnimationFrame(() => { resizePending = false; if (state.view === 'model' && state.report) renderModelEvidence(); else renderCompetition(); });
});
document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
window.addEventListener('pagehide', () => { pause(); if (state.id) fetch(`/api/simulations/${state.id}`, {method: 'DELETE', keepalive: true}).catch(() => null); });

async function initialize() {
  showView(location.hash.slice(1) || 'simulation', false);
  controls();
  try {
    const [metadata, catalogue] = await Promise.all([
      api('/api/metadata'),
      api('/images/catalogue/manifest.json').catch(() => { throw new Error('No se pudo cargar el catálogo de imágenes. Recarga o pulsa Reintentar.'); })
    ]);
    state.catalogueImages = catalogue;
    state.modelAvailable = metadata.model_available;
    if (!metadata.model_available) throw new Error('El modelo aún no está disponible. Ejecuta «python3 -m retail_media train-lab» y vuelve a intentar.');
    $('connection-status').textContent = 'Motor Python conectado';
    await newSimulation();
    loadEvaluation();
  } catch (error) { showError(error.message); }
}
initialize();
