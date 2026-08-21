/** Portal de Ensaios — rascunho local de formulário. */
const _GATILHOS_RASCUNHO = ['qtd_strings', 'qtd_taps', 'qtd_sec', 'qtd_pontos'];
let _restaurandoRascunho = false;

function _chaveRascunho(pagina) { return `rascunho_${pagina}`; }
function _valorCampo(el) {
  if (el.type === 'checkbox') return el.checked;
  if (el.type === 'radio') return el.checked ? el.value : undefined;
  return el.value;
}
function _setCampo(el, valor) {
  if (el.type === 'checkbox') el.checked = !!valor;
  else if (el.type === 'radio') el.checked = el.value === valor;
  else el.value = valor ?? '';
}
function salvarRascunho(pagina) {
  if (_restaurandoRascunho) return;
  const dados = {};
  document.querySelectorAll('input[id], select[id], textarea[id]').forEach(el => {
    const valor = _valorCampo(el);
    if (valor !== undefined) dados[el.id] = valor;
  });
  try { localStorage.setItem(_chaveRascunho(pagina), JSON.stringify({dados, ts: Date.now()})); } catch (_) {}
}
function limparRascunho(pagina) {
  try { localStorage.removeItem(_chaveRascunho(pagina)); } catch (_) {}
}
function restaurarRascunho(pagina) {
  let raw;
  try { raw = localStorage.getItem(_chaveRascunho(pagina)); } catch (_) { return false; }
  if (!raw) return false;
  let dados;
  try { dados = JSON.parse(raw)?.dados; } catch (_) { return false; }
  if (!dados || !Object.keys(dados).length) return false;
  _restaurandoRascunho = true;
  const dispara = el => {
    el.dispatchEvent(new Event('input', {bubbles:true}));
    el.dispatchEvent(new Event('change', {bubbles:true}));
  };
  _GATILHOS_RASCUNHO.forEach(id => {
    const el = document.getElementById(id);
    if (el && Object.prototype.hasOwnProperty.call(dados, id)) { _setCampo(el, dados[id]); dispara(el); }
  });
  Object.keys(dados).forEach(id => {
    if (_GATILHOS_RASCUNHO.includes(id)) return;
    const el = document.getElementById(id);
    if (el) { _setCampo(el, dados[id]); dispara(el); }
  });
  _restaurandoRascunho = false;
  return true;
}
function ativarAutosave(pagina, debounceMs=500) {
  let timer=null;
  document.addEventListener('input', () => {
    clearTimeout(timer);
    timer=setTimeout(() => salvarRascunho(pagina), debounceMs);
  });
  document.addEventListener('change', () => salvarRascunho(pagina));
}
function iniciarRascunho(pagina) {
  const restaurou = restaurarRascunho(pagina);
  if (restaurou && typeof mostrarToast === 'function') mostrarToast('📝 Rascunho anterior restaurado', 'offline');
  ativarAutosave(pagina);
}
