from pydantic import BaseModel
from typing import List, Dict

# --- 1. MODELO ESTATICOS (Trafo, TP, TC) ---
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

# --- 2. MODELO DISJUNTOR MT & SECCIONADORA (300 uOhm | 6 MOhm) ---
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

class EnsaioSeccionadora(EnsaioDisjuntorMT): pass

# --- 3. MODELO DISJUNTOR BT (150 uOhm | 2 MOhm) ---
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