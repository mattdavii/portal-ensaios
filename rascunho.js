/**
 * Rascunho de formulário salvo no localStorage do dispositivo.
 *
 * Objetivo: o técnico não perder dados digitados em campo (app fechado
 * sem querer, sem sinal, tela apagou, celular reiniciou) antes de
 * conseguir enviar o ensaio. É local ao aparelho — não depende de
 * conexão nem do backend — e é independente da fila de sincronização
 * (sync_queue), que já cobre o caso de o ENVIO falhar por falta de
 * internet. Aqui o problema é anterior: preservar o que foi digitado
 * mesmo antes de qualquer tentativa de envio.
 */

// Campos que disparam geração dinâmica de sub-formulário (Qtd Strings,
// Qtd Taps, etc.). Precisam ser restaurados ANTES dos demais, pra
// recriar os campos gerados antes de tentar preenchê-los. Uma página
// que não tiver um desses ids simplesmente não o encontra — a lista é
// compartilhada entre todas as páginas sem problema.
const _GATILHOS_RASCUNHO = ['qtd_strings', 'qtd_taps', 'qtd_sec', 'qtd_pontos'];

let _restaurandoRascunho = false;

function _chaveRascunho(pagina) {
  return `rascunho_${pagina}`;
}

function _valorCampo(el) {
  return (el.type === 'checkbox' || el.type === 'radio') ? el.checked : el.value;
}

function _setCampo(el, valor) {
  if (el.type === 'checkbox' || el.type === 'radio') el.checked = !!valor;
  else el.value = valor;
}

/** Salva todos os campos com id atualmente no DOM. */
function salvarRascunho(pagina) {
  if (_restaurandoRascunho) return;
  const dados = {};
  document.querySelectorAll('input[id], select[id], textarea[id]').forEach(el => {
    dados[el.id] = _valorCampo(el);
  });
  try {
    localStorage.setItem(_chaveRascunho(pagina), JSON.stringify({ dados, ts: Date.now() }));
  } catch (e) {
    // localStorage cheio ou indisponível (modo privado, etc.): autosave
    // vira no-op silencioso — o formulário continua funcionando normalmente,
    // só sem o rascunho.
  }
}

/** Chame depois que o envio (online ou para a fila offline) for concluído. */
function limparRascunho(pagina) {
  try { localStorage.removeItem(_chaveRascunho(pagina)); } catch (e) { /* ignora */ }
}

/** Restaura o rascunho salvo, se existir. Retorna true se havia algo pra restaurar. */
function restaurarRascunho(pagina) {
  let raw;
  try { raw = localStorage.getItem(_chaveRascunho(pagina)); } catch (e) { return false; }
  if (!raw) return false;

  let dados;
  try { dados = JSON.parse(raw).dados; } catch (e) { return false; }
  if (!dados || Object.keys(dados).length === 0) return false;

  _restaurandoRascunho = true;

  const dispara = (el) => {
    // Dispara input/change de verdade (não só seta .value) pra acionar
    // os oninput/onchange já existentes de cada página — geração de
    // sub-campos, cálculos derivados (ex: Rn, distâncias de malha), etc.
    // Assim não é preciso duplicar a lógica de cada formulário aqui.
    el.dispatchEvent(new Event('input', { bubbles: true }));
    el.dispatchEvent(new Event('change', { bubbles: true }));
  };

  // Passo 1 — gatilhos de geração dinâmica primeiro.
  _GATILHOS_RASCUNHO.forEach(id => {
    const el = document.getElementById(id);
    if (el && id in dados) { _setCampo(el, dados[id]); dispara(el); }
  });

  // Passo 2 — todo o resto, incluindo os campos recém-gerados no passo 1.
  Object.keys(dados).forEach(id => {
    if (_GATILHOS_RASCUNHO.includes(id)) return;
    const el = document.getElementById(id);
    if (el) { _setCampo(el, dados[id]); dispara(el); }
  });

  _restaurandoRascunho = false;
  return true;
}

/** Liga o autosave (debounced) pra qualquer alteração de campo na página. */
function ativarAutosave(pagina, debounceMs = 500) {
  let timer = null;
  document.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => salvarRascunho(pagina), debounceMs);
  });
  document.addEventListener('change', () => salvarRascunho(pagina));
}

/**
 * Chame uma vez, no fim do <script> de cada página de ensaio:
 *   iniciarRascunho('nome_da_pagina');
 * Restaura o rascunho salvo (se existir) e liga o autosave dali em diante.
 */
function iniciarRascunho(pagina) {
  const restaurou = restaurarRascunho(pagina);
  if (restaurou && typeof mostrarToast === 'function') {
    mostrarToast('📝 Rascunho anterior restaurado', 'offline');
  }
  ativarAutosave(pagina);
}
