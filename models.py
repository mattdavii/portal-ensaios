from pydantic import BaseModel
from typing import Dict, Optional

class EnsaioCabosCC(BaseModel):
    usina: str; skid: str; inversor: str; tag: str; origem: Optional[str] = "Campo"; destino: Optional[str] = "Campo"
    voc: float; v_pos_terra: float; v_neg_terra: float
    def validar(self) -> Dict:
        def aval(v): return "CONFORME" if v < 120 else "INVESTIGAR STRING"
        return {"status_pos": aval(self.v_pos_terra), "status_neg": aval(self.v_neg_terra), "status_geral": "CONFORME" if max(self.v_pos_terra, self.v_neg_terra) < 120 else "NÃO CONFORME"}

class EnsaioResMalha(BaseModel):
    usina: str; tag: str; metodo: str; d_total: float; r52: float; r62: float; r72: float
    def validar(self) -> Dict:
        media = round((self.r52 + self.r62 + self.r72) / 3, 2)
        desvio = round(max((abs(self.r52 - self.r62)/self.r62)*100, (abs(self.r72 - self.r62)/self.r62)*100), 2) if self.r62 > 0 else 0
        st_plat = "CONFORME" if desvio <= 10.0 else "FALSO PATAMAR"
        st_geral = "CONFORME" if media <= 10.0 and st_plat == "CONFORME" else ("VALOR EQUILIBRADO" if st_plat == "CONFORME" else "REFAZER")
        return {"r_media": media, "desvio": desvio, "status_plat": st_plat, "status_geral": st_geral}

class EnsaioContMalha(BaseModel):
    usina: str; tag: str; pt1_nome: str; pt1_res: float; pt2_nome: str; pt2_res: float; pt3_nome: str; pt3_res: float
    def validar(self) -> Dict:
        def c(v, n): return "NÃO AVALIADO" if n == "" or v == 0 else ("CONFORME" if v <= 1000.0 else "REFAZER")
        st = "REFAZER" if "REFAZER" in [c(self.pt1_res, self.pt1_nome), c(self.pt2_res, self.pt2_nome), c(self.pt3_res, self.pt3_nome)] else "CONFORME"
        return {"status_geral": st}

class EnsaioManobra(BaseModel):
    usina: str; tag: str; fabricante: str
    res_c_r: float; res_c_s: float; res_c_t: float
    iso_ft_r: float; iso_ft_s: float; iso_ft_t: float
    iso_ff_rs: float; iso_ff_st: float; iso_ff_tr: float
    iso_ab_r: float; iso_ab_s: float; iso_ab_t: float

class EnsaioTrafo(BaseModel):
    usina: str; tag: str; tipo: str; tap: str
    nom_pri: float; nom_sec: float; rn_teorico: float
    ttr_a: float; ttr_b: float; ttr_c: float
    h1: float; h2: float; h3: float; uni_h: str
    x1: float; x2: float; x3: float; uni_x: str
    at_t: float; at_bt: float; bt_t: float