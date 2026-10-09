const INFO_ID=`<h6>Temperatura</h6><p>Registre a temperatura do equipamento/enrolamento disponível no momento do ensaio. Ela é importante para comparar medições de resistência ôhmica realizadas em condições diferentes.</p>`;
const INFO_TTR=`<h6>O que é</h6><p>Compara a relação medida pelo TTR com a relação teórica por enrolamento.</p><h6>Ligações</h6><p>As tensões de placa são tensões de linha. Em ligação Estrela, a tensão do enrolamento é a tensão de linha dividida por √3; em Delta, é igual à tensão de linha.</p><h6>Como o Portal avalia</h6><p>O critério interno é <b>0,5%</b>. Até 0,5%: CONFORME. Acima: ATENÇÃO.</p>`;
const INFO_OHMICA=`<h6>O que é</h6><p>Compara as resistências dos enrolamentos/fases para identificar assimetrias.</p><h6>Como o Portal avalia</h6><p>Calcula a média das três fases e o desvio percentual individual de cada leitura. O limite interno é <b>5%</b>. Acima disso: ATENÇÃO.</p><h6>Observação</h6><p>Quando aplicável ao procedimento e ao instrumento utilizado, considerar a desmagnetização do núcleo após o ensaio CC.</p>`;
const INFO_ISO=`<h6>Como o Portal avalia</h6><p><b>≥ 1000 MΩ:</b> CONFORME.<br><b>&lt; 1000 MΩ:</b> APROVADO COM RESSALVA.</p><p>Informe também a tensão aplicada. O valor de 1 GΩ é uma referência interna de boas práticas e deve ser interpretado junto às características e condições do equipamento.</p>`;

function atualizarRelacaoTap(i){
  const relacao=calcularRelacaoTeoricaTrafo(
    numeroCampo(`vpri_${i}`),
    numeroCampo(`vsec_${i}`),
    textoCampo('ligacao_at'),
    textoCampo('ligacao_bt')
  );
  document.getElementById(`rn_${i}`).value=relacao===null?'':relacao.toFixed(6);
}

function atualizarRelacoesTaps(){
  const qtd=Math.min(30,Math.max(0,parseInt(document.getElementById('qtd_taps').value,10)||0));
  for(let i=1;i<=qtd;i++)if(document.getElementById(`rn_${i}`))atualizarRelacaoTap(i);
}

function gerarTaps(){
  const qtd=Math.min(30,Math.max(0,parseInt(document.getElementById('qtd_taps').value,10)||0));
  const container=document.getElementById('taps');
  const atuais={};
  container.querySelectorAll('input[id]').forEach(el=>{atuais[el.id]=el.value;});
  container.innerHTML='';

  for(let i=1;i<=qtd;i++){
    container.insertAdjacentHTML('beforeend',`
      <div class="subcard">
        <div class="row g-2 mb-2">
          <div class="col-3"><input id="tap_${i}" class="form-control dado" value="${i}" placeholder="TAP"></div>
          <div class="col-3"><input type="number" min="0" step="any" id="vpri_${i}" class="form-control dado" placeholder="V prim."></div>
          <div class="col-3"><input type="number" min="0" step="any" id="vsec_${i}" class="form-control dado" placeholder="V sec."></div>
          <div class="col-3"><input id="rn_${i}" class="form-control dado" placeholder="Relação/enrolamento" readonly></div>
        </div>
        <div class="row g-2">
          <div class="col"><input type="number" min="0" step="any" id="ta_${i}" class="form-control dado" placeholder="TTR A"></div>
          <div class="col"><input type="number" min="0" step="any" id="tb_${i}" class="form-control dado" placeholder="TTR B"></div>
          <div class="col"><input type="number" min="0" step="any" id="tc_${i}" class="form-control dado" placeholder="TTR C"></div>
        </div>
      </div>`);
  }

  Object.entries(atuais).forEach(([id,valor])=>{const el=document.getElementById(id);if(el)el.value=valor;});
  for(let i=1;i<=qtd;i++){
    [`vpri_${i}`,`vsec_${i}`].forEach(id=>document.getElementById(id).addEventListener('input',()=>atualizarRelacaoTap(i)));
    atualizarRelacaoTap(i);
  }
}

function formatarMedicaoOhmica(valor,desvio,unidade){
  if(valor===null)return '-';
  return `${valor} ${escaparHtml(unidade)}<br><span style="font-size:.65rem;color:var(--texto-muted)">Desvio: ${desvio===null?'-':desvio.toFixed(2)+'%'}</span>`;
}

function linhaOhmica(nome,rotulos,valores,resultado,unidade){
  return `<tr>
    <td>${nome}</td>
    ${valores.map((valor,i)=>`<td><b>${rotulos[i]}</b><br>${formatarMedicaoOhmica(valor,resultado.desvios[i],unidade)}</td>`).join('')}
    <td>${resultado.media===null?'-':resultado.media.toFixed(6)+' '+escaparHtml(unidade)}</td>
    <td>${badgeStatus(resultado.status)}</td>
  </tr>`;
}

document.getElementById('ligacao_at').addEventListener('change',atualizarRelacoesTaps);
document.getElementById('ligacao_bt').addEventListener('change',atualizarRelacoesTaps);

document.getElementById('formTrafo').addEventListener('submit',async event=>{
  event.preventDefault();
  salvarContextoCampo();

  const qtd=parseInt(document.getElementById('qtd_taps').value,10)||0;
  const ligacaoAt=textoCampo('ligacao_at');
  const ligacaoBt=textoCampo('ligacao_bt');
  const h=[numeroCampo('h1'),numeroCampo('h2'),numeroCampo('h3')];
  const x=[numeroCampo('x1'),numeroCampo('x2'),numeroCampo('x3')];
  const resultadoH=avaliarEquilibrioFases(h);
  const resultadoX=avaliarEquilibrioFases(x);
  const isolamentos=[numeroCampo('at_t'),numeroCampo('at_bt'),numeroCampo('bt_t')];
  const statusIso=statusGeral(isolamentos.map(statusIsolamento));
  const payloads=[];
  const statuses=[resultadoH.status,resultadoX.status,statusIso];
  let linhasTtr='';

  for(let i=1;i<=qtd;i++){
    const relacao=calcularRelacaoTeoricaTrafo(
      numeroCampo(`vpri_${i}`),numeroCampo(`vsec_${i}`),ligacaoAt,ligacaoBt
    );
    const medidos=[numeroCampo(`ta_${i}`),numeroCampo(`tb_${i}`),numeroCampo(`tc_${i}`)];
    const resultado=avaliarTtr(medidos,relacao);
    statuses.push(resultado.status);

    linhasTtr+=`<tr>
      <td>${escaparHtml(textoCampo(`tap_${i}`))}</td>
      <td>${relacao===null?'-':relacao.toFixed(6)}</td>
      ${medidos.map((valor,j)=>`<td>${valor??'-'} (${resultado.erros[j]===null?'-':resultado.erros[j].toFixed(3)+'%'})</td>`).join('')}
      <td>${badgeStatus(resultado.status)}</td>
    </tr>`;

    payloads.push({
      usina:textoCampo('usina'),tag:textoCampo('tag'),tecnico:textoCampo('tecnico')||null,
      os:textoCampo('os')||null,observacoes:textoCampo('observacoes')||null,
      tipo:'TRAFO',tap:textoCampo(`tap_${i}`)||null,
      nom_pri:numeroCampo(`vpri_${i}`),nom_sec:numeroCampo(`vsec_${i}`),rn_teorico:relacao,
      ligacao_at:ligacaoAt,ligacao_bt:ligacaoBt,
      ttr_a:medidos[0],ttr_b:medidos[1],ttr_c:medidos[2],classe:null,finalidade:null,
      h1:h[0],h2:h[1],h3:h[2],uni_h:textoCampo('uni_h'),
      x1:x[0],x2:x[1],x3:x[2],uni_x:textoCampo('uni_x'),
      temperatura_c:numeroCampo('temperatura_c'),at_t:isolamentos[0],at_bt:isolamentos[1],bt_t:isolamentos[2],
      tensao_ensaio_isolamento_v:numeroCampo('tensao_iso')
    });
  }

  await salvarLoteComFila('/api/sync/trafo',payloads,'Transformador salvo');
  limparRascunho('trafo');
  const geral=statusGeral(statuses);
  const nomeLigacao=v=>v==='ESTRELA'?'Estrela (Y)':'Delta (Δ)';

  document.getElementById('laudo_render').innerHTML=`
    ${seloStatus(geral)}
    <div class="header-laudo">
      <b>Usina:</b> ${escaparHtml(textoCampo('usina'))}<br>
      <b>TAG:</b> ${escaparHtml(textoCampo('tag'))} &nbsp; <b>OS:</b> ${escaparHtml(textoCampo('os')||'-')}<br>
      <b>Técnico:</b> ${escaparHtml(textoCampo('tecnico')||'-')}<br>
      <b>Ligação AT/BT:</b> ${nomeLigacao(ligacaoAt)} / ${nomeLigacao(ligacaoBt)}<br>
      <b>Temperatura:</b> ${numeroCampo('temperatura_c')??'-'} °C &nbsp; <b>Data/Hora:</b> ${dataHoraLocalTexto()}
    </div>
    <span class="label-tech">TTR — relação por enrolamento</span>
    <table class="table-laudo"><tr><th>TAP</th><th>Teórica</th><th>A</th><th>B</th><th>C</th><th>Status</th></tr>${linhasTtr}</table>
    <span class="label-tech">Resistência ôhmica</span>
    <table class="table-laudo">
      <tr><th>Enrolamento</th><th>Fase 1</th><th>Fase 2</th><th>Fase 3</th><th>Média</th><th>Status</th></tr>
      ${linhaOhmica('AT',['H1-H3','H2-H1','H3-H2'],h,resultadoH,textoCampo('uni_h'))}
      ${linhaOhmica('BT',['X0-X1','X0-X2','X0-X3'],x,resultadoX,textoCampo('uni_x'))}
    </table>
    <div class="info-strip">Cada desvio é calculado em relação à média das três fases. Critério interno mantido: até 5%.</div>
    <span class="label-tech">Isolamento</span>
    <div class="small mb-2">Tensão aplicada: <b>${numeroCampo('tensao_iso')??'-'} V</b></div>
    <table class="table-laudo"><tr><th>AT-T</th><th>AT-BT</th><th>BT-T</th></tr><tr>${isolamentos.map(v=>`<td>${v===null?'-':v+' MΩ'}<br>${badgeStatus(statusIsolamento(v))}</td>`).join('')}</tr></table>
    <span class="label-tech">Observações</span>
    <div class="observacao-laudo">${escaparHtml(textoCampo('observacoes')||'Sem observações.')}</div>`;

  document.getElementById('box_laudo').classList.remove('d-none');
  document.getElementById('box_laudo').scrollIntoView({behavior:'smooth'});
});

iniciarRascunho('trafo');
setTimeout(()=>{
  gerarTaps();
  restaurarRascunho('trafo');
  atualizarRelacoesTaps();
},0);
