/**
 * Notificação leve (toast) usada no lugar de alert(), que trava a tela
 * e não combina com o visual de instrumento de campo.
 */
function mostrarToast(mensagem, tipo = 'ok') {
  let el = document.getElementById('toastInstrumento');
  if (!el) {
    el = document.createElement('div');
    el.id = 'toastInstrumento';
    document.body.appendChild(el);
  }
  el.textContent = mensagem;
  el.className = `toast-instrumento show ${tipo}`;
  clearTimeout(el._timeoutId);
  el._timeoutId = setTimeout(() => { el.classList.remove('show'); }, 2800);
}
