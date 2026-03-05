import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import database
import models
import uvicorn

app = FastAPI()

# Configuração de CORS para permitir acesso de qualquer origem
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Cria as tabelas no banco de dados SQLite ao iniciar
database.criar_tabelas()


# ==========================================
# ROTAS DE INTERFACE (FRONTEND - PÁGINAS HTML)
# ==========================================
@app.get("/")
def home_dashboard(): 
    return FileResponse("index.html")

@app.get("/trafo")
def pagina_trafo(): 
    return FileResponse("trafo.html")

@app.get("/tp")
def pagina_tp(): 
    return FileResponse("tp.html")

@app.get("/tc")
def pagina_tc(): 
    return FileResponse("tc.html")

@app.get("/disjuntor-mt")
def pagina_disjuntor_mt(): 
    return FileResponse("disjuntor_mt.html")

@app.get("/seccionadora")
def pagina_seccionadora(): 
    return FileResponse("seccionadora.html")

@app.get("/disjuntor-bt")
def pagina_disjuntor_bt(): 
    return FileResponse("disjuntor_bt.html")

@app.get("/cabos-cc")
def pagina_cabos_cc(): return FileResponse("cabos_cc.html")

@app.get("/cont-malha")
def pagina_cont_malha(): return FileResponse("cont_malha.html")

@app.get("/res-malha")
def pagina_res_malha(): return FileResponse("res_malha.html")

# ==========================================
# ROTAS DE API (BACKEND - PROCESSAMENTO DE DADOS)
# ==========================================

# 1. API - Trafos, TPs, TCs (Equipamentos Estáticos)
@app.post("/ensaio/validar")
async def validar_estaticos(d: models.EnsaioTecnico):
    try:
        res = d.validar()
        conn = database.get_db_connection()
        conn.execute("""INSERT INTO ensaio_final 
            (usina, tag, tipo, tap, nom_pri, nom_sec, rn_teorico, ttr_a, ttr_b, ttr_c, status_ttr, 
             h1, h2, h3, uni_h, status_h, x1, x2, x3, uni_x, status_x, at_t, at_bt, bt_t, 
             status_at_t, status_at_bt, status_bt_t) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", 
            (d.usina, d.tag, d.tipo, d.tap, d.nom_pri, d.nom_sec, res['rn_teorico'], 
             d.ttr_medidos[0], d.ttr_medidos[1], d.ttr_medidos[2], res['ttr']['status'], 
             d.h_res[0], d.h_res[1], d.h_res[2], d.h_unidade, res['res_h']['status'], 
             d.x_res[0], d.x_res[1], d.x_res[2], d.x_unidade, res['res_x']['status'], 
             d.at_t, d.at_bt, d.bt_t, 
             res['isolamento']['att'], res['isolamento']['atbt'], res['isolamento']['btt']))
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        print(f"Erro no servidor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 2. API - Disjuntor MT
@app.post("/ensaio/disjuntor-mt/validar")
async def validar_disjuntor_mt(d: models.EnsaioDisjuntorMT):
    try:
        res = d.validar()
        conn = database.get_db_connection()
        conn.execute("""INSERT INTO ensaio_disjuntor_mt 
            (usina, tag, fabricante, res_c_r, res_c_s, res_c_t, status_contato, 
             iso_ft_r, iso_ft_s, iso_ft_t, status_iso_ft, iso_ff_rs, iso_ff_st, iso_ff_tr, status_iso_ff, 
             iso_ab_r, iso_ab_s, iso_ab_t, status_iso_ab) 
            VALUES (?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?)""", 
            (d.usina, d.tag, d.fabricante, d.res_c_r, d.res_c_s, d.res_c_t, res['contato']['status_geral'], 
             d.iso_ft_r, d.iso_ft_s, d.iso_ft_t, res['iso_ft']['r'], 
             d.iso_ff_rs, d.iso_ff_st, d.iso_ff_tr, res['iso_ff']['rs'], 
             d.iso_ab_r, d.iso_ab_s, d.iso_ab_t, res['iso_ab']['r']))
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        print(f"Erro no servidor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 3. API - Seccionadora
@app.post("/ensaio/seccionadora/validar")
async def validar_seccionadora(d: models.EnsaioSeccionadora):
    try:
        res = d.validar()
        conn = database.get_db_connection()
        conn.execute("""INSERT INTO ensaio_seccionadora 
            (usina, tag, fabricante, res_c_r, res_c_s, res_c_t, status_contato, 
             iso_ft_r, iso_ft_s, iso_ft_t, status_iso_ft, iso_ff_rs, iso_ff_st, iso_ff_tr, status_iso_ff, 
             iso_ab_r, iso_ab_s, iso_ab_t, status_iso_ab) 
            VALUES (?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?)""", 
            (d.usina, d.tag, d.fabricante, d.res_c_r, d.res_c_s, d.res_c_t, res['contato']['status_geral'], 
             d.iso_ft_r, d.iso_ft_s, d.iso_ft_t, res['iso_ft']['r'], 
             d.iso_ff_rs, d.iso_ff_st, d.iso_ff_tr, res['iso_ff']['rs'], 
             d.iso_ab_r, d.iso_ab_s, d.iso_ab_t, res['iso_ab']['r']))
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        print(f"Erro no servidor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 4. API - Disjuntor BT
@app.post("/ensaio/disjuntor-bt/validar")
async def validar_disjuntor_bt(d: models.EnsaioDisjuntorBT):
    try:
        res = d.validar()
        conn = database.get_db_connection()
        conn.execute("""INSERT INTO ensaio_disjuntor_bt 
            (usina, tag, fabricante, res_c_r, res_c_s, res_c_t, status_contato, 
             iso_ft_r, iso_ft_s, iso_ft_t, status_iso_ft, iso_ff_rs, iso_ff_st, iso_ff_tr, status_iso_ff, 
             iso_ab_r, iso_ab_s, iso_ab_t, status_iso_ab) 
            VALUES (?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?)""", 
            (d.usina, d.tag, d.fabricante, d.res_c_r, d.res_c_s, d.res_c_t, res['contato']['status_geral'], 
             d.iso_ft_r, d.iso_ft_s, d.iso_ft_t, res['iso_ft']['r'], 
             d.iso_ff_rs, d.iso_ff_st, d.iso_ff_tr, res['iso_ff']['rs'], 
             d.iso_ab_r, d.iso_ab_s, d.iso_ab_t, res['iso_ab']['r']))
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        print(f"Erro no servidor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ensaio/cabos-cc/validar")
async def validar_cabos_cc(d: models.EnsaioCabosCC):
    try:
        res = d.validar()
        conn = database.get_db_connection()
        conn.execute("""INSERT INTO ensaio_cabos_cc 
            (usina, tag, origem, destino, voc, v_pos_terra, v_neg_terra, status_pos, status_neg, status_geral) 
            VALUES (?,?,?,?,?,?,?,?,?,?)""", 
            (d.usina, d.tag, d.origem, d.destino, d.voc, d.v_pos_terra, d.v_neg_terra, res['status_pos'], res['status_neg'], res['status_geral']))
        conn.commit(); conn.close()
        return res
    except Exception as e:
        print(f"Erro no servidor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ensaio/cont-malha/validar")
async def validar_cont_malha(d: models.EnsaioContMalha):
    res = d.validar()
    conn = database.get_db_connection()
    conn.execute("""INSERT INTO ensaio_cont_malha (usina, tag, pt1_nome, pt1_res, pt2_nome, pt2_res, pt3_nome, pt3_res, status_geral) VALUES (?,?,?,?,?,?,?,?,?)""", (d.usina, d.tag, d.pt1_nome, d.pt1_res, d.pt2_nome, d.pt2_res, d.pt3_nome, d.pt3_res, res['status_geral']))
    conn.commit(); conn.close()
    return res

@app.post("/ensaio/res-malha/validar")
async def validar_res_malha(d: models.EnsaioResMalha):
    try:
        res = d.validar()
        conn = database.get_db_connection()
        conn.execute("""INSERT INTO ensaio_res_malha 
            (usina, tag, metodo, d_total, r52, r62, r72, r_media, desvio, status_plat, status_geral) 
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""", 
            (d.usina, d.tag, d.metodo, d.d_total, d.r52, d.r62, d.r72, res['r_media'], res['desvio'], res['status_plat'], res['status_geral']))
        conn.commit()
        conn.close()
        return res
    except Exception as e:
        print(f"Erro no servidor: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Pega a porta injetada pela nuvem (ex: Render). Se rodar localmente no seu PC, ele usa 8000.
    porta = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=porta)