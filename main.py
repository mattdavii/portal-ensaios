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


if __name__ == "__main__":
    # Pega a porta injetada pela nuvem (ex: Render). Se rodar localmente no seu PC, ele usa 8000.
    porta = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=porta)