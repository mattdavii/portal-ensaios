from pydantic import BaseModel
from typing import Dict, Optional

# Limites de validação — Strings CC (ensaio_cabos_cc)
LIMITE_TOQUE_CC = 120.0   # NBR 17193: tensão máx. dentro do arranjo FV. NÃO ALTERAR sem revisão normativa.
TOL_VOC = 0.05            # 5% — tolerância de fabricação do módulo (~±3%) + incerteza de instrumento
TOL_CONSISTENCIA = 0.08   # 8% — provisório, calibrado com amostra pequena (n=4). Recalibrar com mais dados.

class EnsaioCabosCC(BaseModel):
    usina: str; skid: str; inversor: str; tag: str; origem: Optional[str] = "Campo"; destino: Optional[str] = "Campo"
    voc: float; v_pos_terra: float; v_neg_terra: float
    n_modulos: int; voc_stc: float; beta_voc: float; t_medida: float

    def validar(self) -> Dict:
        voc_esperada = round(self.n_modulos * self.voc_stc * (1 + (self.beta_voc / 100) * (self.t_medida - 25)), 2)

        # Critério B — tensão de toque (NBR 17193, limite fixo, não recebe margem)
        def aval_toque(v): return "CONFORME" if v < LIMITE_TOQUE_CC else "INVESTIGAR STRING"
        status_pos = aval_toque(self.v_pos_terra)
        status_neg = aval_toque(self.v_neg_terra)
        ok_toque = self.v_pos_terra < LIMITE_TOQUE_CC and self.v_neg_terra < LIMITE_TOQUE_CC

        # Critério C — consistência do divisor flutuante: (Vpos+Vneg)/VOC deve ser pequeno
        razao_consist = (self.v_pos_terra + self.v_neg_terra) / self.voc if self.voc > 0 else 0.0
        ok_consist = razao_consist <= TOL_CONSISTENCIA
        status_consistencia = "CONFORME" if ok_consist else "FUGA SIMÉTRICA"

        # Critério A — VOC medida vs. esperada (datasheet do módulo corrigido por temperatura)
        desvio_voc = abs(self.voc - voc_esperada) / voc_esperada if voc_esperada > 0 else 0.0
        ok_voc = desvio_voc <= TOL_VOC
        status_voc = "CONFORME" if ok_voc else "VOC FORA DO ESPERADO"

        status_geral = "CONFORME" if (ok_toque and ok_consist and ok_voc) else "NÃO CONFORME"

        return {
            "voc_esperada": voc_esperada,
            "status_pos": status_pos, "status_neg": status_neg,
            "status_consistencia": status_consistencia, "status_voc": status_voc,
            "status_geral": status_geral
        }

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
