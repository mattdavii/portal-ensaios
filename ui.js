/** Portal de Ensaios — utilitários compartilhados. */
const STATUS = Object.freeze({
  CONFORME: 'CONFORME',
  ATENCAO: 'ATENÇÃO',
  RESSALVA: 'APROVADO COM RESSALVA',
  NAO_AVALIADO: 'NÃO AVALIADO',
  REFAZER: 'REFAZER ENSAIO'
});

function mostrarToast(mensagem, tipo='ok') {
  let el=document.getElementById('toastInstrumento');
  if(!el){el=document.createElement('div');el.id='toastInstrumento';document.body.appendChild(el);}
  el.textContent=mensagem; el.className=`toast-instrumento show ${tipo}`;
  clearTimeout(el._timeoutId); el._timeoutId=setTimeout(()=>el.classList.remove('show'),3000);
}
function escaparHtml(valor){return String(valor??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');}
function numeroCampo(id){const el=document.getElementById(id); if(!el||el.value==='')return null; const n=Number(el.value); return Number.isFinite(n)?n:null;}
function textoCampo(id){const el=document.getElementById(id); return el?el.value.trim():'';}
function statusIsolamento(v){if(v===null||v===undefined)return STATUS.NAO_AVALIADO; return Number(v)>=1000?STATUS.CONFORME:STATUS.RESSALVA;}
function classeStatus(s){if(s===STATUS.CONFORME)return'status-conforme';if(s===STATUS.ATENCAO)return'status-atencao';if(s===STATUS.RESSALVA)return'status-ressalva';if(s===STATUS.REFAZER)return'status-refazer';return'status-neutro';}
function badgeStatus(s){return `<span class="status-badge ${classeStatus(s)}">${escaparHtml(s)}</span>`;}
function statusGeral(statuses,{permitirRefazer=false}={}){const v=statuses.filter(Boolean).filter(s=>s!==STATUS.NAO_AVALIADO);if(!v.length)return STATUS.NAO_AVALIADO;if(permitirRefazer&&v.includes(STATUS.REFAZER))return STATUS.REFAZER;if(v.includes(STATUS.ATENCAO))return STATUS.ATENCAO;if(v.includes(STATUS.RESSALVA))return STATUS.RESSALVA;return STATUS.CONFORME;}
function seloStatus(s){const m={
 [STATUS.CONFORME]:['selo-conforme','✓ CONFORME'],
 [STATUS.ATENCAO]:['selo-alerta','⚠ ATENÇÃO'],
 [STATUS.RESSALVA]:['selo-ressalva','⚠ APROVADO COM RESSALVA'],
 [STATUS.REFAZER]:['selo-refazer','✗ REFAZER ENSAIO'],
 [STATUS.NAO_AVALIADO]:['selo-neutro','NÃO AVALIADO']};
 const [c,t]=m[s]||m[STATUS.NAO_AVALIADO]; return `<div class="selo-veredito ${c}">${t}</div>`;}

function garantirModalInfo(){if(document.getElementById('modalInfoPortal'))return;const modal=document.createElement('div');modal.id='modalInfoPortal';modal.className='portal-modal-backdrop';modal.innerHTML=`<div class="portal-modal" role="dialog" aria-modal="true"><div class="portal-modal-header"><strong id="modalInfoTitulo">Informação</strong><button type="button" class="portal-modal-fechar" aria-label="Fechar">×</button></div><div id="modalInfoConteudo" class="portal-modal-body"></div></div>`;document.body.appendChild(modal);const fechar=()=>modal.classList.remove('aberto');modal.querySelector('.portal-modal-fechar').addEventListener('click',fechar);modal.addEventListener('click',e=>{if(e.target===modal)fechar();});document.addEventListener('keydown',e=>{if(e.key==='Escape')fechar();});}
function abrirInfo(titulo,html){garantirModalInfo();document.getElementById('modalInfoTitulo').textContent=titulo;document.getElementById('modalInfoConteudo').innerHTML=html;document.getElementById('modalInfoPortal').classList.add('aberto');}

const CHAVE_CONTEXTO='portal_contexto_campo_v2';
function lerContextoCampo(){try{return JSON.parse(localStorage.getItem(CHAVE_CONTEXTO)||'{}');}catch(_){return{};}}
function salvarContextoCampo(){const atual=lerContextoCampo();const usina=document.getElementById('usina');const tecnico=document.getElementById('tecnico');try{localStorage.setItem(CHAVE_CONTEXTO,JSON.stringify({...atual,usina:usina?.value?.trim()||atual.usina||'',tecnico:tecnico?.value?.trim()||atual.tecnico||''}));}catch(_){}}
function iniciarContextoCampo(){const c=lerContextoCampo();const u=document.getElementById('usina');const t=document.getElementById('tecnico');if(u&&!u.value&&c.usina)u.value=c.usina;if(t&&!t.value&&c.tecnico)t.value=c.tecnico;[u,t].filter(Boolean).forEach(el=>{el.addEventListener('change',salvarContextoCampo);el.addEventListener('blur',salvarContextoCampo);});}

function lerFilaSync(){try{return JSON.parse(localStorage.getItem('sync_queue')||'[]');}catch(_){return[];}}
function gravarFilaSync(f){try{localStorage.setItem('sync_queue',JSON.stringify(f));}catch(_){}}
function enfileirarSync(url,data){const f=lerFilaSync();f.push({id:(crypto?.randomUUID?crypto.randomUUID():`${Date.now()}-${Math.random()}`),url,data,criado_em:new Date().toISOString()});gravarFilaSync(f);}
async function salvarComFilaSilencioso(url,payload){if(navigator.onLine){try{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(r.ok)return true;}catch(_){}}enfileirarSync(url,payload);return false;}
async function salvarComFila(url,payload,mensagemOk='Salvo com sucesso'){const ok=await salvarComFilaSilencioso(url,payload);mostrarToast(ok?`✅ ${mensagemOk}`:'⚠️ Salvo offline — será sincronizado depois',ok?'ok':'offline');return ok;}
async function salvarLoteComFila(url,payloads,mensagemOk='Ensaio salvo'){let on=0,off=0;for(const p of payloads){(await salvarComFilaSilencioso(url,p))?on++:off++;}mostrarToast(off===0?`✅ ${mensagemOk}`:`⚠️ ${off} registro(s) salvo(s) offline`,off===0?'ok':'offline');return{online:on,offline:off};}
async function sincronizarFila(){if(!navigator.onLine){mostrarToast('⚠️ Você está sem internet','offline');return;}const fila=lerFilaSync(),pend=[];for(const item of fila){try{const r=await fetch(item.url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(item.data)});if(!r.ok)pend.push(item);}catch(_){pend.push(item);}}gravarFilaSync(pend);mostrarToast(pend.length?`⚠️ ${pend.length} pendência(s) não enviada(s)`:'✅ Tudo sincronizado',pend.length?'erro':'ok');document.dispatchEvent(new CustomEvent('portal:sync-atualizado'));}

function limparNomeArquivo(t){return String(t||'Registro').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^\w.-]+/g,'_').replace(/_+/g,'_').replace(/^_|_$/g,'');}
function dataArquivo(){const d=new Date(),p=n=>String(n).padStart(2,'0');return`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`;}
function nomeArquivoLaudo(tipo,tag){return`${limparNomeArquivo(textoCampo('usina')||'Usina')}_${limparNomeArquivo(tag||'Ativo')}_${limparNomeArquivo(tipo)}_${dataArquivo()}.pdf`;}
async function baixarPDF(elementId,tipo,tag){if(typeof html2pdf==='undefined'){mostrarToast('Biblioteca de PDF indisponível.','erro');return;}const e=document.getElementById(elementId),nome=nomeArquivoLaudo(tipo,tag);await html2pdf().set({margin:8,filename:nome,image:{type:'jpeg',quality:.98},html2canvas:{scale:2,scrollY:0},jsPDF:{unit:'mm',format:'a4',orientation:'portrait'},pagebreak:{mode:['avoid-all','css','legacy']}}).from(e).save();}
async function compartilharPDF(elementId,tipo,tag){const e=document.getElementById(elementId),nome=nomeArquivoLaudo(tipo,tag);try{const blob=await html2pdf().set({margin:8,filename:nome,image:{type:'jpeg',quality:.98},html2canvas:{scale:2,scrollY:0},jsPDF:{unit:'mm',format:'a4',orientation:'portrait'},pagebreak:{mode:['avoid-all','css','legacy']}}).from(e).output('blob');const arq=new File([blob],nome,{type:'application/pdf'});if(navigator.canShare?.({files:[arq]})){await navigator.share({title:'Registro de Campo',files:[arq]});return;}mostrarToast('Compartilhamento direto não disponível. Baixando o PDF.','offline');await baixarPDF(elementId,tipo,tag);}catch(err){if(err?.name!=='AbortError')mostrarToast('Não foi possível compartilhar o PDF.','erro');}}
function dataHoraLocalTexto(){return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date());}

document.addEventListener('DOMContentLoaded',()=>{garantirModalInfo();iniciarContextoCampo();});
