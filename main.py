import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import database, models, uvicorn

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Garante que o banco de dados é criado
database.criar_tabelas()

# ==========================================
# 1. ROTAS DO FRONTEND (Páginas HTML)
# ==========================================
@app.get("/")
def home(): 
    return FileResponse("index.html")

@app.get("/{pagina}")
def paginas(pagina: str):
    # Lista de páginas permitidas para segurança
    paginas_validas = ["cabos-cc", "res-malha", "cont-malha", "disjuntor-mt", "disjuntor-bt", "seccionadora", "trafo", "tp", "tc"]
    if pagina in paginas_validas:
        nome_arquivo = f"{pagina.replace('-', '_')}.html"
        return FileResponse(nome_arquivo)
    return {"erro": "Página não encontrada"}

# ==========================================
# 2. ROTAS DO PWA (Offline)
# ==========================================
@app.get("/manifest.json")
def manifest(): 
    return FileResponse("manifest.json")

@app.get("/sw.js")
def sw(): 
    return FileResponse("sw.js", media_type="application/javascript")

# ==========================================
# 3. ROTAS DE SINCRONIZAÇÃO (Backend)
# ==========================================
@app.post("/api/sync/cabos-cc")
async def s_cc(d: models.EnsaioCabosCC):
    res = d.validar()
    database.get_db_connection().execute("INSERT INTO ensaio_cabos_cc (usina, skid, inversor, tag, origem, destino, voc, v_pos_terra, v_neg_terra, status_pos, status_neg, status_geral) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (d.usina, d.skid, d.inversor, d.tag, d.origem, d.destino, d.voc, d.v_pos_terra, d.v_neg_terra, res['status_pos'], res['status_neg'], res['status_geral'])).connection.commit()
    return {"status": "ok"}

@app.post("/api/sync/res-malha")
async def s_res(d: models.EnsaioResMalha):
    res = d.validar()
    database.get_db_connection().execute("INSERT INTO ensaio_res_malha (usina, tag, metodo, d_total, r52, r62, r72, r_media, desvio, status_plat, status_geral) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (d.usina, d.tag, d.metodo, d.d_total, d.r52, d.r62, d.r72, res['r_media'], res['desvio'], res['status_plat'], res['status_geral'])).connection.commit()
    return {"status": "ok"}

@app.post("/api/sync/cont-malha")
async def s_cont(d: models.EnsaioContMalha):
    res = d.validar()
    database.get_db_connection().execute("INSERT INTO ensaio_cont_malha (usina, tag, pt1_nome, pt1_res, pt2_nome, pt2_res, pt3_nome, pt3_res, status_geral) VALUES (?,?,?,?,?,?,?,?,?)", (d.usina, d.tag, d.pt1_nome, d.pt1_res, d.pt2_nome, d.pt2_res, d.pt3_nome, d.pt3_res, res['status_geral'])).connection.commit()
    return {"status": "ok"}

def insert_manobra(tabela, d):
    database.get_db_connection().execute(f"INSERT INTO {tabela} (usina, tag, fabricante, res_c_r, res_c_s, res_c_t, iso_ft_r, iso_ft_s, iso_ft_t, iso_ff_rs, iso_ff_st, iso_ff_tr, iso_ab_r, iso_ab_s, iso_ab_t) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (d.usina, d.tag, d.fabricante, d.res_c_r, d.res_c_s, d.res_c_t, d.iso_ft_r, d.iso_ft_s, d.iso_ft_t, d.iso_ff_rs, d.iso_ff_st, d.iso_ff_tr, d.iso_ab_r, d.iso_ab_s, d.iso_ab_t)).connection.commit()

@app.post("/api/sync/disjuntor-mt")
async def s_dmt(d: models.EnsaioManobra): insert_manobra('ensaio_disjuntor_mt', d); return {"status": "ok"}

@app.post("/api/sync/disjuntor-bt")
async def s_dbt(d: models.EnsaioManobra): insert_manobra('ensaio_disjuntor_bt', d); return {"status": "ok"}

@app.post("/api/sync/seccionadora")
async def s_sec(d: models.EnsaioManobra): insert_manobra('ensaio_seccionadora', d); return {"status": "ok"}

@app.post("/api/sync/trafo")
async def s_trafo(d: models.EnsaioTrafo):
    # Lógica de status simplificada para o banco de dados
    st_ttr = "CONFORME" # Na prática, validado no Frontend
    st_h = "AVALIADO"; st_x = "AVALIADO"
    st_at = "CONFORME" if d.at_t >= 1000 else "REFAZER"
    st_atbt = "CONFORME" if d.at_bt >= 1000 else "REFAZER"
    st_btt = "CONFORME" if d.bt_t >= 1000 else "REFAZER"
    
    database.get_db_connection().execute(
        "INSERT INTO ensaio_final (usina, tag, tipo, tap, nom_pri, nom_sec, rn_teorico, ttr_a, ttr_b, ttr_c, status_ttr, h1, h2, h3, uni_h, status_h, x1, x2, x3, uni_x, status_x, at_t, at_bt, bt_t, status_at_t, status_at_bt, status_bt_t) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (d.usina, d.tag, d.tipo, d.tap, d.nom_pri, d.nom_sec, d.rn_teorico, d.ttr_a, d.ttr_b, d.ttr_c, st_ttr, d.h1, d.h2, d.h3, d.uni_h, st_h, d.x1, d.x2, d.x3, d.uni_x, st_x, d.at_t, d.at_bt, d.bt_t, st_at, st_atbt, st_btt)
    ).connection.commit()
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))