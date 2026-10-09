/** Portal de Ensaios — utilitários compartilhados. */
const STATUS = Object.freeze({
  CONFORME: 'CONFORME',
  ATENCAO: 'ATENÇÃO',
  RESSALVA: 'APROVADO COM RESSALVA',
  NAO_AVALIADO: 'NÃO AVALIADO',
  REFAZER: 'REFAZER ENSAIO'
});

const CRITERIOS = Object.freeze({
  ISOLAMENTO_MOHM: 1000,
  TTR_TRAFO_PCT: 0.5,
  OHMICA_TRAFO_PCT: 5,
  DESEQUILIBRIO_CONTATO_PCT: 10,
  ATERRAMENTO_OHM: 10,
  PATAMAR_ATERRAMENTO_PCT: 10,
  CONTINUIDADE_MOHM: 1000
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
function statusIsolamento(v){if(v===null||v===undefined)return STATUS.NAO_AVALIADO; return Number(v)>=CRITERIOS.ISOLAMENTO_MOHM?STATUS.CONFORME:STATUS.RESSALVA;}
function classeStatus(s){if(s===STATUS.CONFORME)return'status-conforme';if(s===STATUS.ATENCAO)return'status-atencao';if(s===STATUS.RESSALVA)return'status-ressalva';if(s===STATUS.REFAZER)return'status-refazer';return'status-neutro';}
function badgeStatus(s){return `<span class="status-badge ${classeStatus(s)}">${escaparHtml(s)}</span>`;}
function statusGeral(statuses,{permitirRefazer=false}={}){const v=statuses.filter(Boolean).filter(s=>s!==STATUS.NAO_AVALIADO);if(!v.length)return STATUS.NAO_AVALIADO;if(permitirRefazer&&v.includes(STATUS.REFAZER))return STATUS.REFAZER;if(v.includes(STATUS.ATENCAO))return STATUS.ATENCAO;if(v.includes(STATUS.RESSALVA))return STATUS.RESSALVA;return STATUS.CONFORME;}

function erroRelativoPct(medido,referencia){
  if(medido===null||medido===undefined||referencia===null||referencia===undefined||Number(referencia)===0)return null;
  const m=Number(medido),r=Number(referencia);
  if(!Number.isFinite(m)||!Number.isFinite(r))return null;
  return Math.abs(m-r)/Math.abs(r)*100;
}

function fatorLigacao(ligacao){
  const valor=String(ligacao||'').trim().toUpperCase();
  if(valor==='ESTRELA'||valor==='Y'||valor==='WYE')return Math.sqrt(3);
  if(valor==='DELTA'||valor==='D'||valor==='Δ')return 1;
  return null;
}

/* As tensões nominais são de linha; o TTR compara a relação por enrolamento. */
function calcularRelacaoTeoricaTrafo(vPrimario,vSecundario,ligacaoAt,ligacaoBt){
  const vp=Number(vPrimario),vs=Number(vSecundario);
  const fatorAt=fatorLigacao(ligacaoAt),fatorBt=fatorLigacao(ligacaoBt);
  if(!Number.isFinite(vp)||!Number.isFinite(vs)||vp<=0||vs<=0||fatorAt===null||fatorBt===null)return null;
  return (vp/fatorAt)/(vs/fatorBt);
}

function avaliarTtr(medidos,referencia,limitePct=CRITERIOS.TTR_TRAFO_PCT){
  const erros=medidos.map(v=>erroRelativoPct(v,referencia));
  const validos=erros.filter(v=>v!==null);
  return {
    erros,
    status:validos.length
      ? (Math.max(...validos)<=limitePct?STATUS.CONFORME:STATUS.ATENCAO)
      : STATUS.NAO_AVALIADO
  };
}

function avaliarEquilibrioFases(valores,limitePct=CRITERIOS.OHMICA_TRAFO_PCT){
  if(valores.length!==3||valores.some(v=>v===null||v===undefined||!Number.isFinite(Number(v)))){
    return {media:null,desvios:[null,null,null],desvioMax:null,status:STATUS.NAO_AVALIADO};
  }
  const numeros=valores.map(Number);
  const media=numeros.reduce((a,b)=>a+b,0)/numeros.length;
  if(media===0)return {media,desvios:[null,null,null],desvioMax:null,status:STATUS.ATENCAO};
  const desvios=numeros.map(v=>Math.abs(v-media)/Math.abs(media)*100);
  const desvioMax=Math.max(...desvios);
  return {media,desvios,desvioMax,status:desvioMax<=limitePct?STATUS.CONFORME:STATUS.ATENCAO};
}

function avaliarContato(valores,limiteOhm,limiteDesequilibrioPct=CRITERIOS.DESEQUILIBRIO_CONTATO_PCT){
  const validos=valores.filter(v=>v!==null&&v!==undefined&&Number.isFinite(Number(v))).map(Number);
  if(!validos.length)return {status:STATUS.NAO_AVALIADO,desequilibrioPct:null};
  const minimo=Math.min(...validos),maximo=Math.max(...validos);
  const desequilibrioPct=minimo>0&&validos.length>=2?((maximo-minimo)/minimo*100):0;
  return {
    status:validos.some(v=>v>limiteOhm)||desequilibrioPct>limiteDesequilibrioPct?STATUS.ATENCAO:STATUS.CONFORME,
    desequilibrioPct
  };
}

function avaliarResistenciaMalha(r52,r62,r72){
  const media=(Number(r52)+Number(r62)+Number(r72))/3;
  const desvioPct=Number(r62)>0
    ? Math.max(Math.abs(Number(r52)-Number(r62))/Number(r62),Math.abs(Number(r72)-Number(r62))/Number(r62))*100
    : null;
  const statusPatamar=desvioPct!==null&&desvioPct<=CRITERIOS.PATAMAR_ATERRAMENTO_PCT?STATUS.CONFORME:STATUS.REFAZER;
  const statusValor=statusPatamar===STATUS.REFAZER
    ? STATUS.NAO_AVALIADO
    : (media<=CRITERIOS.ATERRAMENTO_OHM?STATUS.CONFORME:STATUS.ATENCAO);
  return {
    media,
    desvioPct,
    statusPatamar,
    statusValor,
    statusGeral:statusPatamar===STATUS.REFAZER?STATUS.REFAZER:statusGeral([statusPatamar,statusValor],{permitirRefazer:true})
  };
}
function seloStatus(s){const m={
 [STATUS.CONFORME]:['selo-conforme','✓ CONFORME'],
 [STATUS.ATENCAO]:['selo-alerta','⚠ ATENÇÃO'],
 [STATUS.RESSALVA]:['selo-ressalva','⚠ APROVADO COM RESSALVA'],
 [STATUS.REFAZER]:['selo-refazer','✗ REFAZER ENSAIO'],
 [STATUS.NAO_AVALIADO]:['selo-neutro','NÃO AVALIADO']};
 const [c,t]=m[s]||m[STATUS.NAO_AVALIADO]; return `<div class="selo-veredito ${c}">${t}</div>`;}

function garantirModalInfo(){if(document.getElementById('modalInfoPortal'))return;const modal=document.createElement('div');modal.id='modalInfoPortal';modal.className='portal-modal-backdrop';modal.innerHTML=`<div class="portal-modal" role="dialog" aria-modal="true"><div class="portal-modal-header"><strong id="modalInfoTitulo">Informação</strong><button type="button" class="portal-modal-fechar" aria-label="Fechar">×</button></div><div id="modalInfoConteudo" class="portal-modal-body"></div></div>`;document.body.appendChild(modal);const fechar=()=>modal.classList.remove('aberto');modal.querySelector('.portal-modal-fechar').addEventListener('click',fechar);modal.addEventListener('click',e=>{if(e.target===modal)fechar();});document.addEventListener('keydown',e=>{if(e.key==='Escape')fechar();});}
function abrirInfo(titulo,html){garantirModalInfo();document.getElementById('modalInfoTitulo').textContent=titulo;document.getElementById('modalInfoConteudo').innerHTML=html;document.getElementById('modalInfoPortal').classList.add('aberto');}

const CHAVE_TEMA='portal_tema_v1';
function aplicarTemaPortal(){
  const tema=localStorage.getItem(CHAVE_TEMA)||'claro';
  document.body.classList.toggle('tema-escuro',tema==='escuro');
  const botao=document.querySelector('.tema-toggle');
  if(botao)botao.innerHTML=tema==='escuro'?'☀️ Claro':'🌙 Escuro';
}
function iniciarTemaPortal(){
  if(document.querySelector('.tema-toggle')){aplicarTemaPortal();return;}
  const alvo=document.querySelector('.page-hero-row')||document.querySelector('.topbar');
  if(!alvo)return;
  const botao=document.createElement('button');botao.type='button';botao.className='tema-toggle no-print';botao.setAttribute('aria-label','Alternar tema');
  botao.addEventListener('click',()=>{const novo=document.body.classList.contains('tema-escuro')?'claro':'escuro';localStorage.setItem(CHAVE_TEMA,novo);aplicarTemaPortal();});
  alvo.appendChild(botao);aplicarTemaPortal();
}
function iniciarNavegacaoMobile(){
  if(document.querySelector('.portal-bottom-nav')||location.pathname==='/'||location.pathname==='/index.html')return;
  const nav=document.createElement('nav');nav.className='portal-bottom-nav no-print';nav.setAttribute('aria-label','Navegação rápida');
  const form=document.querySelector('form[id]');
  const laudo=document.getElementById('box_laudo');
  nav.innerHTML=`<a href="/" class="ativo"><strong>⌂</strong><span>Início</span></a>${form?`<a href="#${form.id}"><strong>✎</strong><span>Formulário</span></a>`:''}${laudo?`<a href="#${laudo.id}"><strong>▣</strong><span>Resultado</span></a>`:''}`;
  document.body.appendChild(nav);
  nav.querySelectorAll('a[href^="#"]').forEach(link=>link.addEventListener('click',()=>{nav.querySelectorAll('a').forEach(a=>a.classList.remove('ativo'));link.classList.add('ativo');}));
}
function iniciarEtapasFormulario(){
  const form=document.querySelector('.page-shell form');
  if(!form||form.querySelector('.portal-progress'))return;
  const blocos=[...form.querySelectorAll(':scope > .card-instrumento')];
  if(blocos.length<2)return;
  const nav=document.createElement('nav');nav.className='portal-progress no-print';nav.setAttribute('aria-label','Etapas do ensaio');
  blocos.forEach((bloco,i)=>{const titulo=bloco.querySelector('.label-tech,.section-title-tech')?.textContent?.trim()||`Etapa ${i+1}`;bloco.id=bloco.id||`etapa-${i+1}`;const a=document.createElement('a');a.href=`#${bloco.id}`;a.textContent=`${i+1}. ${titulo}`;if(i===0)a.classList.add('ativo');a.addEventListener('click',()=>{nav.querySelectorAll('a').forEach(x=>x.classList.remove('ativo'));a.classList.add('ativo');});nav.appendChild(a);});
  form.parentElement.insertBefore(nav,form);
}

const CHAVE_CONTEXTO='portal_contexto_campo_v2';
function lerContextoCampo(){try{return JSON.parse(localStorage.getItem(CHAVE_CONTEXTO)||'{}');}catch(_){return{};}}
function salvarContextoCampo(){const atual=lerContextoCampo();const usina=document.getElementById('usina');const tecnico=document.getElementById('tecnico');try{localStorage.setItem(CHAVE_CONTEXTO,JSON.stringify({...atual,usina:usina?.value?.trim()||atual.usina||'',tecnico:tecnico?.value?.trim()||atual.tecnico||''}));}catch(_){}}
function iniciarContextoCampo(){const c=lerContextoCampo();const u=document.getElementById('usina');const t=document.getElementById('tecnico');if(u&&!u.value&&c.usina)u.value=c.usina;if(t&&!t.value&&c.tecnico)t.value=c.tecnico;[u,t].filter(Boolean).forEach(el=>{el.addEventListener('change',salvarContextoCampo);el.addEventListener('blur',salvarContextoCampo);});}

function lerFilaSync(){try{return JSON.parse(localStorage.getItem('sync_queue')||'[]');}catch(_){return[];}}
function gravarFilaSync(f){try{localStorage.setItem('sync_queue',JSON.stringify(f));}catch(_){}}
const CHAVE_RECENTES='portal_ensaios_recentes_v1';
const NOMES_ENSAIO={
  '/api/sync/trafo':'Transformador de potência','/api/sync/tp':'TP','/api/sync/tc':'TC',
  '/api/sync/disjuntor-mt':'Disjuntor MT','/api/sync/disjuntor-bt':'Disjuntor BT','/api/sync/seccionadora':'Seccionadora',
  '/api/sync/res-malha':'Resistência de aterramento','/api/sync/cont-malha':'Continuidade da malha',
  '/api/sync/cabos-cc':'Strings CC','/api/sync/riso-strings':'RISO de Strings','/api/sync/riso-cabos-ca-mt':'RISO de cabos CA/MT',
  '/api/sync/comparador-strings':'Comparador de Strings','/api/sync/desequilibrio-fases':'Desequilíbrio entre fases',
  '/api/sync/voc-string':'Voc de String','/api/sync/relacao-tc-tp':'Relação TC/TP','/api/sync/queda-tensao':'Queda de tensão'
};
function lerEnsaiosRecentes(){try{const v=JSON.parse(localStorage.getItem(CHAVE_RECENTES)||'[]');return Array.isArray(v)?v:[];}catch(_){return[];}}
function gravarEnsaiosRecentes(v){try{localStorage.setItem(CHAVE_RECENTES,JSON.stringify(v.slice(0,12)));}catch(_) {}}
function registrarEnsaioRecente(url,payload){
  const item={id:`${Date.now()}-${Math.random().toString(16).slice(2)}`,url,nome:NOMES_ENSAIO[url]||'Ensaio',usina:payload?.usina||'',tag:payload?.tag||payload?.inversor||'',ts:Date.now()};
  const anteriores=lerEnsaiosRecentes().filter(v=>!(v.url===item.url&&v.tag===item.tag&&v.usina===item.usina));
  gravarEnsaiosRecentes([item,...anteriores]);
  document.dispatchEvent(new CustomEvent('portal:recentes-atualizado'));
}
function enfileirarSync(url,data){const f=lerFilaSync();f.push({id:(globalThis.crypto?.randomUUID?globalThis.crypto.randomUUID():`${Date.now()}-${Math.random()}`),url,data,criado_em:new Date().toISOString()});gravarFilaSync(f);}
async function salvarComFilaSilencioso(url,payload){if(navigator.onLine){try{const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(r.ok){registrarEnsaioRecente(url,payload);return true;}}catch(_){}}enfileirarSync(url,payload);registrarEnsaioRecente(url,payload);return false;}
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
  '/vendor/html2pdf.bundle.min.js',
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
  const conteudo=clone.querySelector('#laudo_render');
  if(conteudo)conteudo.dataset.pdfContent='true';
  clone.querySelectorAll('[id]').forEach(el=>el.removeAttribute('id'));

  const maxCols=_maxColunasTabela(clone);
  const orientacao=original.dataset.pdfOrientation || (maxCols>=8?'landscape':'portrait');
  const larguraMm=orientacao==='landscape'?281:194;

  const host=document.createElement('div');
  host.setAttribute('aria-hidden','true');
  Object.assign(host.style,{
    position:'absolute',
    left:'0',
    top:'-12000px',
    width:`${larguraMm}mm`,
    background:'#ffffff',
    zIndex:'2147483647',
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

  const capture=document.createElement('div');
  Object.assign(capture.style,{
    width:'100%',
    padding:'0 12px',
    boxSizing:'border-box',
    background:'#ffffff',
    overflow:'visible'
  });
  capture.appendChild(clone);
  host.appendChild(capture);
  document.documentElement.appendChild(host);

  return {original,clone,capture,host,orientacao,maxCols};
}

function _escalaPDF(clone){
  const altura=Math.max(clone.scrollHeight,clone.offsetHeight||0);
  const mobile=/Android|iPhone|iPad|iPod/i.test(navigator.userAgent);

  if(altura>9000)return .9;
  if(altura>6000)return 1.0;
  if(altura>3500)return mobile?1.1:1.3;
  return mobile?1.35:1.7;
}

function _dividirTabelaPDF(tabela,maxLinhas){
  const todas=[...tabela.rows];
  if(todas.length<=maxLinhas)return[tabela.cloneNode(true)];

  const cabecalhos=tabela.tHead
    ? [...tabela.tHead.rows]
    : todas.filter((linha,indice)=>indice===0&&[...linha.cells].some(c=>c.tagName==='TH'));
  const corpo=todas.filter(linha=>!cabecalhos.includes(linha));
  if(!corpo.length)return[tabela.cloneNode(true)];

  const partes=[];
  for(let inicio=0;inicio<corpo.length;inicio+=maxLinhas){
    const parte=tabela.cloneNode(false);
    if(cabecalhos.length){
      const thead=document.createElement('thead');
      cabecalhos.forEach(linha=>thead.appendChild(linha.cloneNode(true)));
      parte.appendChild(thead);
    }
    const tbody=document.createElement('tbody');
    corpo.slice(inicio,inicio+maxLinhas).forEach(linha=>tbody.appendChild(linha.cloneNode(true)));
    parte.appendChild(tbody);
    partes.push(parte);
  }
  return partes;
}

function _blocosRelatorioPDF(clone,orientacao){
  const raiz=clone.querySelector('[data-pdf-content="true"]');
  const origens=[];
  [...clone.children].forEach(filho=>{
    if(filho===raiz)origens.push(...filho.children);
    else origens.push(filho);
  });

  const maxLinhas=orientacao==='landscape'?12:16;
  return origens.flatMap(bloco=>bloco.tagName==='TABLE'
    ? _dividirTabelaPDF(bloco,maxLinhas)
    : [bloco.cloneNode(true)]
  );
}

function _relatorioExigeSegmentacao(clone){
  if(Math.max(clone.scrollHeight,clone.offsetHeight||0)>4200)return true;
  return [...clone.querySelectorAll('table')].some(t=>t.rows.length>18);
}

function _recortarMargensVerticaisCanvas(canvas){
  try{
    const contexto=canvas.getContext('2d',{willReadFrequently:true});
    const pixels=contexto.getImageData(0,0,canvas.width,canvas.height).data;
    let primeiro=-1,ultimo=-1;
    for(let y=0;y<canvas.height;y++){
      let possuiConteudo=false;
      for(let x=0;x<canvas.width;x+=3){
        const i=(y*canvas.width+x)*4;
        if(pixels[i+3]>10&&(pixels[i]<248||pixels[i+1]<248||pixels[i+2]<248)){
          possuiConteudo=true;
          break;
        }
      }
      if(possuiConteudo){
        if(primeiro<0)primeiro=y;
        ultimo=y;
      }
    }
    if(primeiro<0||ultimo<primeiro)return canvas;
    const margem=Math.max(4,Math.round(canvas.width*.008));
    const inicio=Math.max(0,primeiro-margem);
    const fim=Math.min(canvas.height,ultimo+margem+1);
    if(inicio===0&&fim===canvas.height)return canvas;
    const recortado=document.createElement('canvas');
    recortado.width=canvas.width;
    recortado.height=fim-inicio;
    recortado.getContext('2d').drawImage(canvas,0,inicio,canvas.width,recortado.height,0,0,canvas.width,recortado.height);
    return recortado;
  }catch(_){
    return canvas;
  }
}

async function _gerarPDFSegmentado(ctx,nome){
  if(typeof globalThis.html2pdf!=='function')throw new Error('Componente de paginação do PDF indisponível.');
  const iniciador=document.createElement('div');
  Object.assign(iniciador.style,{position:'absolute',left:'0',top:'0',width:'1px',height:'1px',background:'#fff',overflow:'hidden'});
  ctx.host.appendChild(iniciador);
  const baseWorker=globalThis.html2pdf().set({
    margin:0,
    image:{type:'jpeg',quality:.92},
    html2canvas:{scale:1,backgroundColor:'#ffffff',logging:false},
    jsPDF:{unit:'mm',format:'a4',orientation:ctx.orientacao,compress:true}
  }).from(iniciador).toPdf();
  const pdf=await baseWorker.get('pdf');
  iniciador.remove();
  const segmentHost=document.createElement('div');
  Object.assign(segmentHost.style,{
    position:'absolute',
    left:'0',
    top:'0',
    width:ctx.orientacao==='landscape'?'281mm':'194mm',
    background:'#ffffff',
    zIndex:'2147483647',
    pointerEvents:'none'
  });
  document.documentElement.appendChild(segmentHost);
  ctx.segmentHost=segmentHost;
  const margem={top:8,right:8,bottom:10,left:8};
  const paginaW=pdf.internal.pageSize.getWidth();
  const paginaH=pdf.internal.pageSize.getHeight();
  const utilW=paginaW-margem.left-margem.right;
  const utilH=paginaH-margem.top-margem.bottom;
  let y=margem.top;
  let primeiraPagina=true;

  const novaPagina=()=>{
    if(primeiraPagina)primeiraPagina=false;
    else pdf.addPage();
    y=margem.top;
  };
  novaPagina();

  const adicionarCanvas=canvas=>{
    const alturaMm=canvas.height*utilW/canvas.width;
    if(alturaMm<=paginaH-margem.bottom-y){
      pdf.addImage(canvas.toDataURL('image/jpeg',.92),'JPEG',margem.left,y,utilW,alturaMm,undefined,'FAST');
      y+=alturaMm+2;
      return;
    }
    if(alturaMm<=utilH){
      novaPagina();
      pdf.addImage(canvas.toDataURL('image/jpeg',.92),'JPEG',margem.left,y,utilW,alturaMm,undefined,'FAST');
      y+=alturaMm+2;
      return;
    }

    let origemY=0;
    while(origemY<canvas.height){
      if(y>margem.top+1)novaPagina();
      const fatiaPx=Math.min(canvas.height-origemY,Math.max(1,Math.floor(canvas.width*utilH/utilW)));
      const fatia=document.createElement('canvas');
      fatia.width=canvas.width;
      fatia.height=fatiaPx;
      fatia.getContext('2d').drawImage(canvas,0,origemY,canvas.width,fatiaPx,0,0,canvas.width,fatiaPx);
      const fatiaHmm=fatiaPx*utilW/canvas.width;
      pdf.addImage(fatia.toDataURL('image/jpeg',.92),'JPEG',margem.left,margem.top,utilW,fatiaHmm,undefined,'FAST');
      origemY+=fatiaPx;
      y=margem.top+fatiaHmm+2;
      if(origemY<canvas.height)novaPagina();
    }
  };

  const blocos=_blocosRelatorioPDF(ctx.clone,ctx.orientacao);
  for(const bloco of blocos){
    const superficie=document.createElement('div');
    Object.assign(superficie.style,{
      width:'100%',
      padding:'0 12px',
      boxSizing:'border-box',
      background:'#fff',
      color:'#1c2128'
    });
    superficie.appendChild(bloco);
    segmentHost.appendChild(superficie);
    await _esperarRecursosPDF(superficie);
    const canvasWorker=globalThis.html2pdf().set({html2canvas:{
        scale:/Android|iPhone|iPad|iPod/i.test(navigator.userAgent)?1.2:1.5,
        useCORS:true,
        allowTaint:false,
        backgroundColor:'#ffffff',
        logging:false,
        scrollX:0,
        scrollY:0,
        windowWidth:Math.ceil(superficie.scrollWidth||ctx.host.scrollWidth)
      }}).from(superficie).toCanvas();
    const canvas=_recortarMargensVerticaisCanvas(await canvasWorker.get('canvas'));
    superficie.remove();
    if(canvas.width&&canvas.height)adicionarCanvas(canvas);
  }

  const blob=pdf.output('blob');
  if(!(blob instanceof Blob)||blob.size<1000)throw new Error(`O PDF ${nome} ficou vazio ou inválido.`);
  return blob;
}

async function _gerarBlobPDF(elementId,tipo,tag){
  const bibliotecaOk=await garantirBibliotecaPDF();
  if(!bibliotecaOk)throw new Error('Biblioteca de PDF indisponível. Atualize o Portal e tente novamente.');

  const nome=nomeArquivoLaudo(tipo,tag);
  const ctx=_prepararElementoPDF(elementId);

  try{
    await _esperarRecursosPDF(ctx.capture);
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
        windowWidth:Math.ceil(ctx.capture.scrollWidth||ctx.host.scrollWidth)
      },
      jsPDF:{unit:'mm',format:'a4',orientation:ctx.orientacao,compress:true},
      pagebreak:{mode:['css','legacy'],avoid:['tr','.selo-veredito','.header-laudo']}
    });

    let blob;
    const escalaInicial=_escalaPDF(ctx.capture);

    try{
      if(_relatorioExigeSegmentacao(ctx.clone)){
        blob=await _gerarPDFSegmentado(ctx,nome);
      }else{
        const worker=globalThis.html2pdf().set(criarOpcoes(escalaInicial)).from(ctx.capture).toPdf();
        blob=await worker.outputPdf('blob');
      }
    }catch(erroInicial){
      if(escalaInicial<=.8)throw erroInicial;
      const workerLeve=globalThis.html2pdf().set(criarOpcoes(.8)).from(ctx.capture).toPdf();
      blob=await workerLeve.outputPdf('blob');
    }

    if(!(blob instanceof Blob)||blob.size<1000)throw new Error('O PDF gerado ficou vazio ou inválido.');
    return {blob,nome};
  }finally{
    ctx.segmentHost?.remove();
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

document.addEventListener('DOMContentLoaded',()=>{garantirModalInfo();iniciarContextoCampo();iniciarTemaPortal();iniciarNavegacaoMobile();iniciarEtapasFormulario();});
