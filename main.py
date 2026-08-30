import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import uvicorn
import database, models

app=FastAPI(title='Portal de Ensaios',docs_url=None,redoc_url=None,openapi_url=None)
database.criar_tabelas()
PAGINAS={'queda-tensao':'queda_tensao.html','relacao-tc-tp':'relacao_tc_tp.html','voc-string':'voc_string.html','desequilibrio-fases':'desequilibrio_fases.html','riso-cabos-ca-mt':'riso_cabos_ca_mt.html','comparador-strings':'comparador_strings.html','riso-strings':'riso_strings.html','cabos-cc':'cabos_cc.html','res-malha':'res_malha.html','cont-malha':'cont_malha.html','disjuntor-mt':'disjuntor_mt.html','disjuntor-bt':'disjuntor_bt.html','seccionadora':'seccionadora.html','trafo':'trafo.html','tp':'tp.html','tc':'tc.html','conversor-resistencia':'conversor_resistencia.html'}

def _file(path,media=None,cache='no-cache'):
    kw={'headers':{'Cache-Control':cache}}
    if media:kw['media_type']=media
    return FileResponse(path,**kw)

def _exec(sql,valores):
    conn=database.get_db_connection()
    try:conn.execute(sql,valores);conn.commit()
    finally:conn.close()

@app.get('/health')
def health():return {'status':'ok'}
@app.api_route('/',methods=['GET','HEAD'])
def home():return _file('index.html')
@app.api_route('/sw.js',methods=['GET','HEAD'])
def sw():return _file('sw.js','application/javascript')
@app.api_route('/manifest.json',methods=['GET','HEAD'])
def manifest():return _file('manifest.json','application/manifest+json')
@app.api_route('/style.css',methods=['GET','HEAD'])
def style():return _file('style.css','text/css')
@app.api_route('/ui.js',methods=['GET','HEAD'])
def ui():return _file('ui.js','application/javascript')
@app.api_route('/rascunho.js',methods=['GET','HEAD'])
def rascunho():return _file('rascunho.js','application/javascript')
@app.api_route('/resistencia.js',methods=['GET','HEAD'])
def resistencia():return _file('resistencia.js','application/javascript')
@app.api_route('/logo.png',methods=['GET','HEAD'])
def logo():return _file('logo.png','image/png','public, max-age=86400')
@app.api_route('/{pagina}',methods=['GET','HEAD'])
def pagina(pagina:str):
    if pagina in PAGINAS:return _file(PAGINAS[pagina])
    raise HTTPException(404,'Página não encontrada')

@app.post('/api/sync/cabos-cc')
def s_cc(d:models.EnsaioCabosCC):
    r=d.validar()

    _exec("""INSERT INTO ensaio_cabos_cc (
        usina,
        skid,
        inversor,
        tag,
        origem,
        destino,
        voc,
        v_pos_terra,
        v_neg_terra,
        n_modulos,
        voc_stc,
        beta_voc,
        t_medida,
        temperatura_modulo,
        tolerancia_voc,
        voc_esperada,
        pct_pos_terra,
        pct_neg_terra,
        pct_max_terra,
        faixa_diagnostico,
        diagnostico,
        status_consistencia,
        status_voc,
        status_geral,
        tecnico,
        os,
        observacoes,
        status_geral_v2
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
        d.usina,
        d.skid,
        d.inversor,
        d.tag,
        d.origem,
        d.destino,
        d.voc,
        d.v_pos_terra,
        d.v_neg_terra,
        d.n_modulos,
        d.voc_stc,
        d.beta_voc,
        d.temperatura_modulo,
        d.temperatura_modulo,
        d.tolerancia_voc,
        r['voc_esperada'],
        r['pct_pos_terra'],
        r['pct_neg_terra'],
        r['pct_max_terra'],
        r['faixa_diagnostico'],
        r['diagnostico'],
        r['status_diagnostico'],
        r['status_voc'],
        r['status_geral'],
        d.tecnico,
        d.os,
        d.observacoes,
        r['status_geral']
    ))

    return {'status':'ok','resultado':r}


@app.post('/api/sync/riso-strings')
def s_riso_strings(d:models.EnsaioRisoString):
    r=d.validar()

    _exec("""INSERT INTO ensaio_riso_strings (
        usina,
        tag,
        inversor,
        riso_pn_mohm,
        riso_pos_mohm,
        riso_neg_mohm,
        tensao_ensaio_v,
        status_pn,
        status_pos,
        status_neg,
        status_geral,
        tecnico,
        os,
        observacoes
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
        d.usina,
        d.tag,
        d.inversor,
        d.riso_pn_mohm,
        d.riso_pos_mohm,
        d.riso_neg_mohm,
        d.tensao_ensaio_v,
        r['status_pn'],
        r['status_pos'],
        r['status_neg'],
        r['status_geral'],
        d.tecnico,
        d.os,
        d.observacoes
    ))

    return {'status':'ok','resultado':r}


@app.post('/api/sync/res-malha')
def s_rm(d:models.EnsaioResMalha):
    r=d.validar();_exec('''INSERT INTO ensaio_res_malha (usina,tag,metodo,d_total,r52,r62,r72,r_media,desvio,status_plat,status_valor,status_geral,tecnico,os,observacoes,status_geral_v2) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(d.usina,d.tag,d.metodo,d.d_total,d.r52,d.r62,d.r72,r['r_media'],r['desvio_pct'],r['status_patamar'],r['status_valor'],r['status_geral'],d.tecnico,d.os,d.observacoes,r['status_geral']))
    return {'status':'ok','resultado':r}

@app.post('/api/sync/cont-malha')
def s_cm(d:models.EnsaioContMalha):
    r=d.validar();_exec('''INSERT INTO ensaio_cont_malha (usina,tag,pt1_nome,pt1_res,pt2_nome,pt2_res,pt3_nome,pt3_res,status_geral,tecnico,os,observacoes,status_geral_v2) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',(d.usina,d.tag,d.pt1_nome,d.pt1_res,d.pt2_nome,d.pt2_res,d.pt3_nome,d.pt3_res,r['status_geral'],d.tecnico,d.os,d.observacoes,r['status_geral']))
    return {'status':'ok','resultado':r}

def _manobra(tabela,d,limite):
    r=d.validar(limite)
    _exec(f'''INSERT INTO {tabela} (usina,tag,fabricante,res_c_r,res_c_s,res_c_t,status_contato,iso_ft_r,iso_ft_s,iso_ft_t,status_iso_ft,iso_ff_rs,iso_ff_st,iso_ff_tr,status_iso_ff,iso_ab_r,iso_ab_s,iso_ab_t,status_iso_ab,corrente_ensaio_a,tensao_ensaio_isolamento_v,desequilibrio_pct,tecnico,os,observacoes,status_geral_v2) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(d.usina,d.tag,d.fabricante,d.res_c_r,d.res_c_s,d.res_c_t,r['status_contato'],d.iso_ft_r,d.iso_ft_s,d.iso_ft_t,r['status_isolamento'],d.iso_ff_rs,d.iso_ff_st,d.iso_ff_tr,r['status_isolamento'],d.iso_ab_r,d.iso_ab_s,d.iso_ab_t,r['status_isolamento'],d.corrente_ensaio_a,d.tensao_ensaio_isolamento_v,r['desequilibrio_pct'],d.tecnico,d.os,d.observacoes,r['status_geral']))
    return {'status':'ok','resultado':r}
@app.post('/api/sync/disjuntor-mt')
def s_dmt(d:models.EnsaioManobra):return _manobra('ensaio_disjuntor_mt',d,models.LIMITE_CONTATO_MT_UOHM)
@app.post('/api/sync/disjuntor-bt')
def s_dbt(d:models.EnsaioManobra):return _manobra('ensaio_disjuntor_bt',d,models.LIMITE_CONTATO_BT_UOHM)
@app.post('/api/sync/seccionadora')
def s_sec(d:models.EnsaioManobra):return _manobra('ensaio_seccionadora',d,models.LIMITE_CONTATO_SECCIONADORA_UOHM)

@app.post('/api/sync/trafo')
def s_trafo(d:models.EnsaioTrafo):
    r=d.validar()
    sa=models.status_isolamento(d.at_t)
    sab=models.status_isolamento(d.at_bt)
    sbt=models.status_isolamento(d.bt_t)

    _exec('''INSERT INTO ensaio_final (
        usina,tag,tipo,tap,nom_pri,nom_sec,rn_teorico,
        ttr_a,ttr_b,ttr_c,status_ttr,
        h1,h2,h3,uni_h,status_h,
        x1,x2,x3,uni_x,status_x,
        at_t,at_bt,bt_t,status_at_t,status_at_bt,status_bt_t,
        classe,finalidade,temperatura_c,tensao_ensaio_isolamento_v,
        limite_ttr_pct,tecnico,os,observacoes,status_geral_v2,
        quantidade_secundarios,secundarios_json
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(
        d.usina,d.tag,d.tipo,d.tap,d.nom_pri,d.nom_sec,d.rn_teorico,
        d.ttr_a,d.ttr_b,d.ttr_c,r['status_ttr'],
        d.h1,d.h2,d.h3,d.uni_h,r['status_h'],
        d.x1,d.x2,d.x3,d.uni_x,r['status_x'],
        d.at_t,d.at_bt,d.bt_t,sa,sab,sbt,
        d.classe,d.finalidade,d.temperatura_c,d.tensao_ensaio_isolamento_v,
        r['limite_ttr_pct'],d.tecnico,d.os,d.observacoes,r['status_geral'],
        d.quantidade_secundarios,d.secundarios_json
    ))

    return {'status':'ok','resultado':r}


@app.post('/api/sync/riso-cabos-ca-mt')
def s_riso_cabos_ca_mt(d:models.EnsaioRisoCabosCaMt):
    r=d.validar()
    _exec("""INSERT INTO ensaio_riso_cabos_ca_mt (
        usina,tag,classe_circuito,tensao_ensaio_v,r_terra,s_terra,t_terra,rs,st,tr,
        status_r_terra,status_s_terra,status_t_terra,status_rs,status_st,status_tr,status_geral,
        tecnico,os,observacoes
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",(
        d.usina,d.tag,d.classe_circuito,d.tensao_ensaio_v,d.r_terra,d.s_terra,d.t_terra,d.rs,d.st,d.tr,
        r['status_r_terra'],r['status_s_terra'],r['status_t_terra'],r['status_rs'],r['status_st'],r['status_tr'],r['status_geral'],
        d.tecnico,d.os,d.observacoes
    ))
    return {'status':'ok','resultado':r}

if __name__=='__main__':uvicorn.run(app,host='0.0.0.0',port=int(os.environ.get('PORT',8000)))
