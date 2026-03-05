from pydantic import BaseModel
from typing import List, Dict

# ==========================================
# 1. ESTATICOS (Transformador, TP, TC)
# ==========================================
class EnsaioTecnico(BaseModel):
    usina: str; tag: str; tipo: str; tap: str
    nom_pri: float; nom_sec: float
    ttr_medidos: List[float]; h_res: List[float]; h_unidade: str; x_res: List[float]; x_unidade: str
    at_t: float; at_bt: float; bt_t: float

    def validar(self) -> Dict:
        rn_teorico = self.nom_pri / self.nom_sec if self.nom_sec > 0 else 0
        erros_fases = [round(abs((m - rn_teorico) / rn_teorico) * 100, 3) if rn_teorico > 0 and m > 0 else 0 for m in self.ttr_medidos]
        status_ttr = "NÃO AVALIADO" if sum(self.ttr_medidos) == 0 else ("CONFORME" if max(erros_fases) <= 0.5 else "NÃO CONFORME")

        f = {"uOhm": 0.001, "mOhm": 1.0, "Ohm": 1000.0}
        h_m = [v * f[self.h_unidade] for v in self.h_res if v > 0]
        x_m = [v * f[self.x_unidade] for v in self.x_res if v > 0]

        def get_eval(l_m, l_o):
            if sum(l_o) == 0: return 0, "NÃO AVALIADO"
            if len(l_m) == 1: return 0, "REGISTRADO"
            if len(l_m) < 2: return 0, "DADOS INSUFICIENTES"
            d = ((max(l_m) - min(l_m)) / min(l_m)) * 100
            return round(d, 2), ("CONFORME" if d <= 10 else "NÃO CONFORME")

        des_h, st_h = get_eval(h_m, self.h_res)
        des_x, st_x = get_eval(x_m, self.x_res)

        v_at = 5000 if self.nom_pri > 5000 and self.tipo == "Transformador" else 1000
        v_bt = 50 if self.tipo in ["TC", "TP"] else (1000 if self.nom_sec >= 800 else 500)
        
        def aval_iso(val, lim): return "NÃO AVALIADO" if val == 0 else ("CONFORME" if (val * 1000) >= lim else "REFAZER")

        return {
            "rn_teorico": round(rn_teorico, 4),
            "ttr": {"medidos": self.ttr_medidos, "erros": erros_fases, "status": status_ttr},
            "res_h": {"medidos": self.h_res, "unidade": self.h_unidade, "desvio": des_h, "status": st_h},
            "res_x": {"medidos": self.x_res, "unidade": self.x_unidade, "desvio": des_x, "status": st_x},
            "isolamento": {"att": aval_iso(self.at_t, (v_at/1000)+1), "atbt": aval_iso(self.at_bt, (v_at/1000)+1), "btt": aval_iso(self.bt_t, (v_bt/1000)+1)}
        }

# ==========================================
# 2. DISJUNTOR MT & SECCIONADORA (300 uOhm | 6 MOhm)
# ==========================================
class EnsaioDisjuntorMT(BaseModel):
    usina: str; tag: str; fabricante: str
    res_c_r: float; res_c_s: float; res_c_t: float
    iso_ft_r: float; iso_ft_s: float; iso_ft_t: float
    iso_ff_rs: float; iso_ff_st: float; iso_ff_tr: float
    iso_ab_r: float; iso_ab_s: float; iso_ab_t: float

    def validar(self) -> Dict:
        def a_c(v): return "NÃO AVALIADO" if v == 0 else ("CONFORME" if v <= 300 else "REFAZER")
        def a_i(v): return "NÃO AVALIADO" if v == 0 else ("CONFORME" if v >= 0.006 else "REFAZER")
        
        c_r, c_s, c_t = a_c(self.res_c_r), a_c(self.res_c_s), a_c(self.res_c_t)
        st_c = "REFAZER" if "REFAZER" in [c_r, c_s, c_t] else ("CONFORME" if sum([self.res_c_r, self.res_c_s, self.res_c_t]) > 0 else "NÃO AVALIADO")
        
        return {
            "contato": {"r": c_r, "s": c_s, "t": c_t, "status_geral": st_c},
            "iso_ft": {"r": a_i(self.iso_ft_r), "s": a_i(self.iso_ft_s), "t": a_i(self.iso_ft_t)},
            "iso_ff": {"rs": a_i(self.iso_ff_rs), "st": a_i(self.iso_ff_st), "tr": a_i(self.iso_ff_tr)},
            "iso_ab": {"r": a_i(self.iso_ab_r), "s": a_i(self.iso_ab_s), "t": a_i(self.iso_ab_t)}
        }

class EnsaioSeccionadora(EnsaioDisjuntorMT): 
    pass # Herda exatamente as mesmas regras do Disjuntor MT

# ==========================================
# 3. DISJUNTOR BT (150 uOhm | 2 MOhm)
# ==========================================
class EnsaioDisjuntorBT(EnsaioDisjuntorMT):
    def validar(self) -> Dict:
        def a_c(v): return "NÃO AVALIADO" if v == 0 else ("CONFORME" if v <= 150 else "REFAZER")
        def a_i(v): return "NÃO AVALIADO" if v == 0 else ("CONFORME" if v >= 0.002 else "REFAZER")
        
        c_r, c_s, c_t = a_c(self.res_c_r), a_c(self.res_c_s), a_c(self.res_c_t)
        st_c = "REFAZER" if "REFAZER" in [c_r, c_s, c_t] else ("CONFORME" if sum([self.res_c_r, self.res_c_s, self.res_c_t]) > 0 else "NÃO AVALIADO")
        
        return {
            "contato": {"r": c_r, "s": c_s, "t": c_t, "status_geral": st_c},
            "iso_ft": {"r": a_i(self.iso_ft_r), "s": a_i(self.iso_ft_s), "t": a_i(self.iso_ft_t)},
            "iso_ff": {"rs": a_i(self.iso_ff_rs), "st": a_i(self.iso_ff_st), "tr": a_i(self.iso_ff_tr)},
            "iso_ab": {"r": a_i(self.iso_ab_r), "s": a_i(self.iso_ab_s), "t": a_i(self.iso_ab_t)}
        }

# ==========================================
# 4. CABOS CC STRINGS (Fuga para o Terra < 120V)
# ==========================================
class EnsaioCabosCC(BaseModel):
    usina: str; tag: str; origem: str; destino: str
    voc: float; v_pos_terra: float; v_neg_terra: float

    def validar(self) -> Dict:
        def aval_queda(v): return "NÃO AVALIADO" if v == 0 else ("CONFORME" if v < 120 else "INVESTIGAR STRING")
        st_pos = aval_queda(self.v_pos_terra)
        st_neg = aval_queda(self.v_neg_terra)

        if "INVESTIGAR STRING" in [st_pos, st_neg]: st_geral = "NÃO CONFORME"
        elif st_pos == "CONFORME" or st_neg == "CONFORME": st_geral = "CONFORME"
        else: st_geral = "NÃO AVALIADO"

        return {"voc": self.voc if self.voc > 0 else "N/A", "status_pos": st_pos, "status_neg": st_neg, "status_geral": st_geral}

# ==========================================
# 5. CONTINUIDADE DE MALHA (<= 1000 mOhm)
# ==========================================
class EnsaioContMalha(BaseModel):
    usina: str; tag: str
    pt1_nome: str; pt1_res: float
    pt2_nome: str; pt2_res: float
    pt3_nome: str; pt3_res: float

    def validar(self) -> Dict:
        # ATUALIZADO: O limite agora é 1000 mOhm (que equivale a 1 Ohm)
        def a_c(v, nome): return "NÃO AVALIADO" if nome == "" or v == 0 else ("CONFORME" if v <= 1000.0 else "REFAZER")
        
        c1, c2, c3 = a_c(self.pt1_res, self.pt1_nome), a_c(self.pt2_res, self.pt2_nome), a_c(self.pt3_res, self.pt3_nome)
        
        st_geral = "REFAZER" if "REFAZER" in [c1, c2, c3] else ("CONFORME" if any(x != "NÃO AVALIADO" for x in [c1, c2, c3]) else "NÃO AVALIADO")
        return {"p1": c1, "p2": c2, "p3": c3, "status_geral": st_geral}

# ==========================================
# 6. RESISTÊNCIA DE MALHA TERRÔMETRO (Patamar 62%)
# ==========================================
class EnsaioResMalha(BaseModel):
    usina: str; tag: str; metodo: str
    d_total: float; r52: float; r62: float; r72: float

    def validar(self) -> Dict:
        if self.r52 == 0 and self.r62 == 0 and self.r72 == 0:
            return {"r_media": 0, "desvio": 0, "status_plat": "NÃO AVALIADO", "status_geral": "NÃO AVALIADO"}

        medicoes = [self.r52, self.r62, self.r72]
        r_media = round(sum(medicoes) / 3, 2)
        
        # LÓGICA CORRIGIDA: Compara os extremos com o valor central (62%)
        if self.r62 > 0:
            desvio_52 = (abs(self.r52 - self.r62) / self.r62) * 100
            desvio_72 = (abs(self.r72 - self.r62) / self.r62) * 100
            # Pega o pior desvio entre as duas hastes
            desvio = round(max(desvio_52, desvio_72), 2)
        else:
            desvio = 0

        # Regras Normativas
        status_plat = "CONFORME" if desvio <= 10.0 else "FALSO PATAMAR"
        status_geral = "CONFORME" if r_media <= 10.0 and status_plat == "CONFORME" else "REFAZER"

        return {
            "r_media": r_media,
            "desvio": desvio,
            "status_plat": status_plat,
            "status_geral": status_geral
        }