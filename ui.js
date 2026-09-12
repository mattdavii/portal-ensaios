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
function enfileirarSync(url,data){const f=lerFilaSync();f.push({id:(globalThis.crypto?.randomUUID?globalThis.crypto.randomUUID():`${Date.now()}-${Math.random()}`),url,data,criado_em:new Date().toISOString()});gravarFilaSync(f);}
async function salvarComFilaSilencioso(url,payload){if(navigator.onLine){try{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(r.ok)return true;}catch(_){}}enfileirarSync(url,payload);return false;}
async function salvarComFila(url,payload,mensagemOk='Salvo com sucesso'){const ok=await salvarComFilaSilencioso(url,payload);mostrarToast(ok?`✅ ${mensagemOk}`:'⚠️ Salvo offline — será sincronizado depois',ok?'ok':'offline');return ok;}
async function salvarLoteComFila(url,payloads,mensagemOk='Ensaio salvo'){let on=0,off=0;for(const p of payloads){(await salvarComFilaSilencioso(url,p))?on++:off++;}mostrarToast(off===0?`✅ ${mensagemOk}`:`⚠️ ${off} registro(s) salvo(s) offline`,off===0?'ok':'offline');return{online:on,offline:off};}
async function sincronizarFila(){if(!navigator.onLine){mostrarToast('⚠️ Você está sem internet','offline');return;}const fila=lerFilaSync(),pend=[];for(const item of fila){try{const r=await fetch(item.url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(item.data)});if(!r.ok)pend.push(item);}catch(_){pend.push(item);}}gravarFilaSync(pend);mostrarToast(pend.length?`⚠️ ${pend.length} pendência(s) não enviada(s)`:'✅ Tudo sincronizado',pend.length?'erro':'ok');document.dispatchEvent(new CustomEvent('portal:sync-atualizado'));}

function limparNomeArquivo(t){return String(t||'Registro').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/[^\w.-]+/g,'_').replace(/_+/g,'_').replace(/^_|_$/g,'');}
function dataArquivo(){const d=new Date(),p=n=>String(n).padStart(2,'0');return`${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}`;}
function nomeArquivoLaudo(tipo,tag){return`${limparNomeArquivo(textoCampo('usina')||'Usina')}_${limparNomeArquivo(tag||'Ativo')}_${limparNomeArquivo(tipo)}_${dataArquivo()}.pdf`;}

/* --------------------------------------------------------------------------
 * PDF — geração robusta para desktop, Android/iOS e relatórios longos.
 * ----------------------------------------------------------------------- */
const PDF_CDNS=[
  'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js',
  'https://cdn.jsdelivr.net/npm/html2pdf.js@0.10.1/dist/html2pdf.bundle.min.js'
];
let _pdfBibliotecaPromise=null;
let _pdfEmProcesso=false;

function _esperar(ms){return new Promise(resolve=>setTimeout(resolve,ms));}

async function garantirBibliotecaPDF(){
  if(typeof globalThis.html2pdf==='function')return true;
  if(_pdfBibliotecaPromise)return _pdfBibliotecaPromise;

  _pdfBibliotecaPromise=(async()=>{
    for(const src of PDF_CDNS){
      try{
        await new Promise((resolve,reject)=>{
          const existente=[...document.scripts].find(s=>s.src===src);
          if(existente){
            if(typeof globalThis.html2pdf==='function'){resolve();return;}
            const timeout=setTimeout(()=>reject(new Error('timeout')),8000);
            existente.addEventListener('load',()=>{clearTimeout(timeout);resolve();},{once:true});
            existente.addEventListener('error',()=>{clearTimeout(timeout);reject(new Error('erro'))},{once:true});
            return;
          }

          const script=document.createElement('script');
          script.src=src;
          script.async=true;
          const timeout=setTimeout(()=>{script.remove();reject(new Error('timeout'));},8000);
          script.onload=()=>{clearTimeout(timeout);resolve();};
          script.onerror=()=>{clearTimeout(timeout);script.remove();reject(new Error('erro'));};
          document.head.appendChild(script);
        });
        if(typeof globalThis.html2pdf==='function')return true;
      }catch(_){/* tenta o próximo CDN */}
    }
    return false;
  })();

  const ok=await _pdfBibliotecaPromise;
  if(!ok)_pdfBibliotecaPromise=null;
  return ok;
}

async function _esperarRecursosPDF(elemento){
  if(document.fonts?.ready){
    try{await Promise.race([document.fonts.ready,_esperar(1500)]);}catch(_){}
  }

  const imagens=[...elemento.querySelectorAll('img')].filter(img=>!img.complete);
  if(imagens.length){
    await Promise.race([
      Promise.all(imagens.map(img=>new Promise(resolve=>{
        img.addEventListener('load',resolve,{once:true});
        img.addEventListener('error',resolve,{once:true});
      }))),
      _esperar(2500)
    ]);
  }
}

function _maxColunasTabela(elemento){
  let max=0;
  elemento.querySelectorAll('tr').forEach(tr=>{max=Math.max(max,tr.children.length);});
  return max;
}

function _prepararElementoPDF(elementId){
  const original=document.getElementById(elementId);
  if(!original)throw new Error(`Elemento ${elementId} não encontrado.`);

  const clone=original.cloneNode(true);
  clone.removeAttribute('id');
  clone.classList.remove('d-none','mt-3','mt-4');

  clone.querySelectorAll('.no-print').forEach(el=>el.remove());
  clone.querySelectorAll('[id]').forEach(el=>el.removeAttribute('id'));

  const maxCols=_maxColunasTabela(clone);
  const orientacao=original.dataset.pdfOrientation || (maxCols>=8?'landscape':'portrait');
  const larguraMm=orientacao==='landscape'?281:194;

  const host=document.createElement('div');
  host.setAttribute('aria-hidden','true');
  Object.assign(host.style,{
    position:'absolute',
    left:'-12000px',
    top:'0',
    width:`${larguraMm}mm`,
    background:'#ffffff',
    zIndex:'-9999',
    overflow:'visible',
    pointerEvents:'none'
  });

  Object.assign(clone.style,{
    display:'block',
    width:'100%',
    maxWidth:'none',
    margin:'0',
    boxShadow:'none',
    background:'#ffffff',
    color:'#1c2128',
    overflow:'visible'
  });

  clone.querySelectorAll('.table-laudo').forEach(table=>{
    table.style.width='100%';
    table.style.maxWidth='100%';
    table.style.tableLayout=maxCols>=8?'fixed':'auto';
    table.style.fontSize=maxCols>=8?'.62rem':'.72rem';
  });
  clone.querySelectorAll('.table-laudo th,.table-laudo td').forEach(cell=>{
    cell.style.padding=maxCols>=8?'4px 3px':'5px';
    cell.style.whiteSpace='normal';
    cell.style.overflowWrap='anywhere';
    cell.style.wordBreak='normal';
  });
  clone.querySelectorAll('tr,.selo-veredito,.header-laudo,.observacao-laudo').forEach(el=>{
    el.style.breakInside='avoid';
    el.style.pageBreakInside='avoid';
  });

  host.appendChild(clone);
  document.body.appendChild(host);

  return {original,clone,host,orientacao,maxCols};
}

function _escalaPDF(clone){
  const altura=Math.max(clone.scrollHeight,clone.offsetHeight||0);
  const mobile=/Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

  if(altura>9000)return .9;
  if(altura>6000)return 1.0;
  if(altura>3500)return mobile?1.1:1.3;
  return mobile?1.35:1.7;
}

async function _gerarBlobPDF(elementId,tipo,tag){
  const bibliotecaOk=await garantirBibliotecaPDF();
  if(!bibliotecaOk)throw new Error('Biblioteca de PDF indisponível. Conecte-se à internet e tente novamente.');

  const nome=nomeArquivoLaudo(tipo,tag);
  const ctx=_prepararElementoPDF(elementId);

  try{
    await _esperarRecursosPDF(ctx.clone);
    await _esperar(40);

    const criarOpcoes=escala=>({
      margin:[8,8,10,8],
      filename:nome,
      image:{type:'jpeg',quality:escala<=.9?.90:.95},
      html2canvas:{
        scale:escala,
        useCORS:true,
        allowTaint:false,
        backgroundColor:'#ffffff',
        logging:false,
        scrollX:0,
        scrollY:0,
        windowWidth:Math.ceil(ctx.clone.scrollWidth||ctx.host.scrollWidth)
      },
      jsPDF:{unit:'mm',format:'a4',orientation:ctx.orientacao,compress:true},
      pagebreak:{mode:['css','legacy'],avoid:['tr','.selo-veredito','.header-laudo']}
    });

    let blob;
    const escalaInicial=_escalaPDF(ctx.clone);

    try{
      const worker=globalThis.html2pdf().set(criarOpcoes(escalaInicial)).from(ctx.clone).toPdf();
      blob=await worker.outputPdf('blob');
    }catch(erroInicial){
      if(escalaInicial<=.8)throw erroInicial;
      const workerLeve=globalThis.html2pdf().set(criarOpcoes(.8)).from(ctx.clone).toPdf();
      blob=await workerLeve.outputPdf('blob');
    }

    if(!(blob instanceof Blob)||blob.size<1000)throw new Error('O PDF gerado ficou vazio ou inválido.');
    return {blob,nome};
  }finally{
    ctx.host.remove();
  }
}

function _baixarBlob(blob,nome){
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url;
  a.download=nome;
  a.rel='noopener';
  a.style.display='none';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),30000);
}

async function baixarPDF(elementId,tipo,tag){
  if(_pdfEmProcesso){mostrarToast('O PDF já está sendo gerado. Aguarde.','offline');return;}
  _pdfEmProcesso=true;
  mostrarToast('Gerando PDF...','offline');

  try{
    const {blob,nome}=await _gerarBlobPDF(elementId,tipo,tag);
    _baixarBlob(blob,nome);
    mostrarToast('✅ PDF gerado com sucesso.','ok');
  }catch(err){
    console.error('Falha ao gerar PDF:',err);
    mostrarToast(err?.message||'Não foi possível gerar o PDF.','erro');
  }finally{
    _pdfEmProcesso=false;
  }
}

async function compartilharPDF(elementId,tipo,tag){
  if(_pdfEmProcesso){mostrarToast('O PDF já está sendo gerado. Aguarde.','offline');return;}
  _pdfEmProcesso=true;
  mostrarToast('Preparando PDF...','offline');

  try{
    const {blob,nome}=await _gerarBlobPDF(elementId,tipo,tag);
    const arquivo=typeof File==='function'?new File([blob],nome,{type:'application/pdf'}):null;

    if(arquivo&&navigator.share&&navigator.canShare?.({files:[arquivo]})){
      await navigator.share({title:'Registro de Campo',files:[arquivo]});
      return;
    }

    mostrarToast('Compartilhamento direto indisponível. O PDF será baixado.','offline');
    _baixarBlob(blob,nome);
  }catch(err){
    if(err?.name==='AbortError')return;
    console.error('Falha ao compartilhar PDF:',err);
    mostrarToast(err?.message||'Não foi possível compartilhar o PDF.','erro');
  }finally{
    _pdfEmProcesso=false;
  }
}

function dataHoraLocalTexto(){return new Intl.DateTimeFormat('pt-BR',{dateStyle:'short',timeStyle:'short'}).format(new Date());}

document.addEventListener('DOMContentLoaded',()=>{garantirModalInfo();iniciarContextoCampo();});
