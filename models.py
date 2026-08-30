import json
from typing import Optional, Dict, List
from pydantic import BaseModel

STATUS_CONFORME = "CONFORME"
STATUS_ATENCAO = "ATENÇÃO"
STATUS_RESSALVA = "APROVADO COM RESSALVA"
STATUS_NAO_AVALIADO = "NÃO AVALIADO"
STATUS_REFAZER = "REFAZER ENSAIO"

LIMITE_ISOLAMENTO_MOHM = 1000.0
LIMITE_CONTATO_MT_UOHM = 300.0
LIMITE_CONTATO_BT_UOHM = 150.0
LIMITE_CONTATO_SECCIONADORA_UOHM = 300.0
TOL_DESEQUILIBRIO_CONTATO = 0.10
TOL_OHMICA_TRAFO = 0.05
TOL_TTR_TRAFO = 0.005
LIMITE_ATERRAMENTO_OHM = 10.0
TOL_PATAMAR_ATERRAMENTO = 0.10
LIMITE_CONTINUIDADE_MOHM = 1000.0
LIMITE_POLO_TERRA_CONFORME = 0.10
LIMITE_POLO_TERRA_ELEVADO = 0.15


def status_isolamento(valor: Optional[float]) -> str:
    if valor is None:
        return STATUS_NAO_AVALIADO
    return STATUS_CONFORME if valor >= LIMITE_ISOLAMENTO_MOHM else STATUS_RESSALVA


def status_geral(statuses: List[str], permitir_refazer: bool = False) -> str:
    validos = [s for s in statuses if s and s != STATUS_NAO_AVALIADO]
    if not validos:
        return STATUS_NAO_AVALIADO
    if permitir_refazer and STATUS_REFAZER in validos:
        return STATUS_REFAZER
    if STATUS_ATENCAO in validos:
        return STATUS_ATENCAO
    if STATUS_RESSALVA in validos:
        return STATUS_RESSALVA
    return STATUS_CONFORME


def erro_relativo(medido: Optional[float], referencia: Optional[float]) -> Optional[float]:
    if medido is None or referencia in (None, 0):
        return None
    return abs(medido - referencia) / abs(referencia)


def limite_classe_instrumento(tipo: str, classe: Optional[str]) -> Optional[float]:
    if not classe:
        return None
    c = classe.strip().upper().replace(",", ".")
    try:
        return float(c)
    except ValueError:
        pass
    if tipo.upper() == "TP":
        if c == "3P": return 3.0
        if c == "6P": return 6.0
    if tipo.upper() == "TC":
        if c.startswith("5P"): return 1.0
        if c.startswith("10P"): return 3.0
    return None


class MetadadosCampo(BaseModel):
    usina: str
    tag: str
    tecnico: Optional[str] = None
    os: Optional[str] = None
    observacoes: Optional[str] = None


class EnsaioCabosCC(MetadadosCampo):
    skid: Optional[str] = None
    inversor: Optional[str] = None
    origem: Optional[str] = "Campo"
    destino: Optional[str] = "Campo"
    voc: float
    v_pos_terra: float
    v_neg_terra: float
    n_modulos: int
    voc_stc: float
    beta_voc: float
    temperatura_modulo: float
    tolerancia_voc: float = 0.05

    def validar(self) -> Dict:
        voc_esperada = self.n_modulos * self.voc_stc * (
            1 + (self.beta_voc / 100.0) * (self.temperatura_modulo - 25.0)
        )

        desvio_voc = (
            abs(self.voc - voc_esperada) / abs(voc_esperada)
            if voc_esperada else None
        )

        status_voc = (
            STATUS_CONFORME
            if desvio_voc is not None and desvio_voc <= self.tolerancia_voc
            else STATUS_ATENCAO
        )

        voc_abs = abs(self.voc)
        vp_abs = abs(self.v_pos_terra)
        vn_abs = abs(self.v_neg_terra)

        pct_pos_terra = vp_abs / voc_abs if voc_abs > 0 else None
        pct_neg_terra = vn_abs / voc_abs if voc_abs > 0 else None

        pct_max_terra = (
            max(pct_pos_terra, pct_neg_terra)
            if pct_pos_terra is not None and pct_neg_terra is not None
            else None
        )

        if pct_max_terra is None:
            status_diagnostico = STATUS_NAO_AVALIADO
            faixa_diagnostico = "NÃO AVALIADO"
            diagnostico = "Dados insuficientes para avaliação do diagnóstico polo-terra."

        elif pct_max_terra <= LIMITE_POLO_TERRA_CONFORME:
            status_diagnostico = STATUS_CONFORME
            faixa_diagnostico = "ATÉ 10%"
            diagnostico = (
                "As tensões polo-terra permanecem baixas em relação à Voc medida da string."
            )

        elif pct_max_terra <= LIMITE_POLO_TERRA_ELEVADO:
            status_diagnostico = STATUS_ATENCAO
            faixa_diagnostico = "ENTRE 10% E 15%"
            diagnostico = (
                "Uma das tensões polo-terra encontra-se entre 10% e 15% da Voc medida. "
                "O resultado requer atenção e avaliação técnica."
            )

        else:
            status_diagnostico = STATUS_ATENCAO
            faixa_diagnostico = "ACIMA DE 15%"
            diagnostico = (
                "Uma das tensões polo-terra supera 15% da Voc medida. "
                "Foi identificado desvio elevado neste diagnóstico auxiliar."
            )

        geral = status_geral([status_voc, status_diagnostico])

        return {
            "voc_esperada": round(voc_esperada, 2),
            "desvio_voc_pct": round((desvio_voc or 0) * 100, 2),

            "pct_pos_terra": (
                round(pct_pos_terra * 100, 2)
                if pct_pos_terra is not None else None
            ),
            "pct_neg_terra": (
                round(pct_neg_terra * 100, 2)
                if pct_neg_terra is not None else None
            ),
            "pct_max_terra": (
                round(pct_max_terra * 100, 2)
                if pct_max_terra is not None else None
            ),

            "faixa_diagnostico": faixa_diagnostico,
            "status_voc": status_voc,
            "status_diagnostico": status_diagnostico,
            "diagnostico": diagnostico,
            "status_geral": geral,
        }



class EnsaioRisoString(MetadadosCampo):
    inversor: Optional[str] = None

    riso_pn_mohm: float
    riso_pos_mohm: float
    riso_neg_mohm: float

    tensao_ensaio_v: float

    def validar(self) -> Dict:
        status_pn = status_isolamento(self.riso_pn_mohm)
        status_pos = status_isolamento(self.riso_pos_mohm)
        status_neg = status_isolamento(self.riso_neg_mohm)

        return {
            "status_pn": status_pn,
            "status_pos": status_pos,
            "status_neg": status_neg,
            "status_geral": status_geral([
                status_pn,
                status_pos,
                status_neg
            ]),
        }


class EnsaioResMalha(MetadadosCampo):
    metodo: str = "62%"
    d_total: float
    r52: float
    r62: float
    r72: float

    def validar(self) -> Dict:
        media = (self.r52 + self.r62 + self.r72) / 3.0
        if self.r62 <= 0:
            desvio = None
            status_patamar = STATUS_REFAZER
        else:
            desvio = max(abs(self.r52 - self.r62) / self.r62, abs(self.r72 - self.r62) / self.r62)
            status_patamar = STATUS_CONFORME if desvio <= TOL_PATAMAR_ATERRAMENTO else STATUS_REFAZER
        if status_patamar == STATUS_REFAZER:
            status_valor = STATUS_NAO_AVALIADO
            geral = STATUS_REFAZER
        else:
            status_valor = STATUS_CONFORME if media <= LIMITE_ATERRAMENTO_OHM else STATUS_ATENCAO
            geral = status_geral([status_patamar, status_valor], permitir_refazer=True)
        return {"r_media": round(media,3), "desvio_pct": round((desvio or 0)*100,2), "status_patamar": status_patamar, "status_valor": status_valor, "status_geral": geral}


class EnsaioContMalha(MetadadosCampo):
    pt1_nome: str
    pt1_res: Optional[float] = None
    pt2_nome: Optional[str] = None
    pt2_res: Optional[float] = None
    pt3_nome: Optional[str] = None
    pt3_res: Optional[float] = None

    def _ponto(self, nome, valor):
        if not nome or valor is None: return STATUS_NAO_AVALIADO
        return STATUS_CONFORME if valor <= LIMITE_CONTINUIDADE_MOHM else STATUS_ATENCAO

    def validar(self) -> Dict:
        sts=[self._ponto(self.pt1_nome,self.pt1_res),self._ponto(self.pt2_nome,self.pt2_res),self._ponto(self.pt3_nome,self.pt3_res)]
        return {"status_pt1":sts[0],"status_pt2":sts[1],"status_pt3":sts[2],"status_geral":status_geral(sts)}


class EnsaioManobra(MetadadosCampo):
    fabricante: Optional[str] = None
    corrente_ensaio_a: Optional[float] = None
    res_c_r: Optional[float] = None
    res_c_s: Optional[float] = None
    res_c_t: Optional[float] = None
    iso_ft_r: Optional[float] = None
    iso_ft_s: Optional[float] = None
    iso_ft_t: Optional[float] = None
    iso_ff_rs: Optional[float] = None
    iso_ff_st: Optional[float] = None
    iso_ff_tr: Optional[float] = None
    iso_ab_r: Optional[float] = None
    iso_ab_s: Optional[float] = None
    iso_ab_t: Optional[float] = None
    tensao_ensaio_isolamento_v: Optional[float] = None

    def validar(self, limite_contato_uohm: float) -> Dict:
        contatos=[v for v in [self.res_c_r,self.res_c_s,self.res_c_t] if v is not None]
        if not contatos:
            status_contato=STATUS_NAO_AVALIADO; desequilibrio=None
        else:
            minimo,maximo=min(contatos),max(contatos)
            desequilibrio=((maximo-minimo)/minimo) if minimo>0 and len(contatos)>=2 else 0.0
            status_contato=STATUS_ATENCAO if any(v>limite_contato_uohm for v in contatos) or desequilibrio>TOL_DESEQUILIBRIO_CONTATO else STATUS_CONFORME
        isolamentos=[self.iso_ft_r,self.iso_ft_s,self.iso_ft_t,self.iso_ff_rs,self.iso_ff_st,self.iso_ff_tr,self.iso_ab_r,self.iso_ab_s,self.iso_ab_t]
        status_iso=status_geral([status_isolamento(v) for v in isolamentos])
        return {"limite_contato_uohm":limite_contato_uohm,"desequilibrio_pct":round((desequilibrio or 0)*100,2),"status_contato":status_contato,"status_isolamento":status_iso,"status_geral":status_geral([status_contato,status_iso])}


class EnsaioTrafo(MetadadosCampo):
    tipo: str
    tap: Optional[str] = None
    nom_pri: Optional[float] = None
    nom_sec: Optional[float] = None
    rn_teorico: Optional[float] = None
    ttr_a: Optional[float] = None
    ttr_b: Optional[float] = None
    ttr_c: Optional[float] = None
    classe: Optional[str] = None
    finalidade: Optional[str] = None
    h1: Optional[float] = None
    h2: Optional[float] = None
    h3: Optional[float] = None
    uni_h: Optional[str] = None
    x1: Optional[float] = None
    x2: Optional[float] = None
    x3: Optional[float] = None
    uni_x: Optional[str] = None
    temperatura_c: Optional[float] = None
    at_t: Optional[float] = None
    at_bt: Optional[float] = None
    bt_t: Optional[float] = None
    tensao_ensaio_isolamento_v: Optional[float] = None

    quantidade_secundarios: Optional[int] = None
    secundarios_json: Optional[str] = None

    def validar(self) -> Dict:
        tipo = self.tipo.upper()

        def equilibrio(vals):
            validos = [v for v in vals if v is not None]
            if len(validos) < 3:
                return {"status": STATUS_NAO_AVALIADO, "desvio": None}
            media = sum(validos) / 3
            if media == 0:
                return {"status": STATUS_ATENCAO, "desvio": None}
            d = max(abs(v - media) / abs(media) for v in validos)
            return {
                "status": STATUS_CONFORME if d <= TOL_OHMICA_TRAFO else STATUS_ATENCAO,
                "desvio": d * 100,
            }

        # Transformador de potência mantém a lógica original.
        if tipo == "TRAFO":
            limite_pct = TOL_TTR_TRAFO * 100
            erros = []

            for medido in [self.ttr_a, self.ttr_b, self.ttr_c]:
                e = erro_relativo(medido, self.rn_teorico)
                erros.append(None if e is None else e * 100)

            ev = [e for e in erros if e is not None]

            status_ttr = (
                STATUS_NAO_AVALIADO
                if not ev
                else (STATUS_CONFORME if max(ev) <= limite_pct else STATUS_ATENCAO)
            )

            eqh = equilibrio([self.h1, self.h2, self.h3])
            eqx = equilibrio([self.x1, self.x2, self.x3])

            status_iso = status_geral([
                status_isolamento(self.at_t),
                status_isolamento(self.at_bt),
                status_isolamento(self.bt_t),
            ])

            return {
                "limite_ttr_pct": limite_pct,
                "erro_ttr_a_pct": None if erros[0] is None else round(erros[0], 3),
                "erro_ttr_b_pct": None if erros[1] is None else round(erros[1], 3),
                "erro_ttr_c_pct": None if erros[2] is None else round(erros[2], 3),
                "status_ttr": status_ttr,
                "status_h": eqh["status"],
                "desvio_h_pct": None if eqh["desvio"] is None else round(eqh["desvio"], 2),
                "status_x": eqx["status"],
                "desvio_x_pct": None if eqx["desvio"] is None else round(eqx["desvio"], 2),
                "status_isolamento": status_iso,
                "status_geral": status_geral([
                    status_ttr, eqh["status"], eqx["status"], status_iso
                ]),
            }

        # TP/TC novos: cada secundário possui classe e limite percentual próprios.
        secundarios = []

        if self.secundarios_json:
            try:
                dados = json.loads(self.secundarios_json)
                if isinstance(dados, list):
                    secundarios = dados
            except (TypeError, ValueError, json.JSONDecodeError):
                secundarios = []

        if secundarios:
            erros = []
            status_relacoes = []
            status_isos = [status_isolamento(self.at_t)]

            for sec in secundarios:
                rn = sec.get("rn_teorico")
                medido = sec.get("relacao_medida")
                tolerancia = sec.get("tolerancia_pct")

                e = erro_relativo(medido, rn)
                erro_pct = None if e is None else e * 100
                erros.append(erro_pct)

                if erro_pct is None or tolerancia is None:
                    st_rel = STATUS_NAO_AVALIADO
                else:
                    try:
                        limite = float(tolerancia)
                        st_rel = STATUS_CONFORME if erro_pct <= limite else STATUS_ATENCAO
                    except (TypeError, ValueError):
                        st_rel = STATUS_NAO_AVALIADO

                status_relacoes.append(st_rel)

                status_isos.append(status_isolamento(sec.get("riso_prim_sec")))
                status_isos.append(status_isolamento(sec.get("riso_sec_terra")))

            status_ttr = status_geral(status_relacoes)
            status_iso = status_geral(status_isos)

            limite_unico = None
            if len(secundarios) == 1:
                try:
                    tol = secundarios[0].get("tolerancia_pct")
                    limite_unico = None if tol is None else float(tol)
                except (TypeError, ValueError):
                    limite_unico = None

            erros_compat = (erros + [None, None, None])[:3]

            return {
                "limite_ttr_pct": limite_unico,
                "erro_ttr_a_pct": None if erros_compat[0] is None else round(erros_compat[0], 3),
                "erro_ttr_b_pct": None if erros_compat[1] is None else round(erros_compat[1], 3),
                "erro_ttr_c_pct": None if erros_compat[2] is None else round(erros_compat[2], 3),
                "status_ttr": status_ttr,
                "status_h": STATUS_NAO_AVALIADO,
                "desvio_h_pct": None,
                "status_x": STATUS_NAO_AVALIADO,
                "desvio_x_pct": None,
                "status_isolamento": status_iso,
                "status_geral": status_geral([status_ttr, status_iso]),
            }

        # Compatibilidade com registros antigos de TP/TC.
        limite_pct = limite_classe_instrumento(tipo, self.classe)
        erros = []

        for medido in [self.ttr_a, self.ttr_b, self.ttr_c]:
            e = erro_relativo(medido, self.rn_teorico)
            erros.append(None if e is None else e * 100)

        ev = [e for e in erros if e is not None]

        status_ttr = (
            STATUS_NAO_AVALIADO
            if not ev or limite_pct is None
            else (STATUS_CONFORME if max(ev) <= limite_pct else STATUS_ATENCAO)
        )

        status_iso = status_geral([
            status_isolamento(self.at_t),
            status_isolamento(self.at_bt),
            status_isolamento(self.bt_t),
        ])

        return {
            "limite_ttr_pct": limite_pct,
            "erro_ttr_a_pct": None if erros[0] is None else round(erros[0], 3),
            "erro_ttr_b_pct": None if erros[1] is None else round(erros[1], 3),
            "erro_ttr_c_pct": None if erros[2] is None else round(erros[2], 3),
            "status_ttr": status_ttr,
            "status_h": STATUS_NAO_AVALIADO,
            "desvio_h_pct": None,
            "status_x": STATUS_NAO_AVALIADO,
            "desvio_x_pct": None,
            "status_isolamento": status_iso,
            "status_geral": status_geral([status_ttr, status_iso]),
        }



class EnsaioRisoCabosCaMt(MetadadosCampo):
    classe_circuito: str
    tensao_ensaio_v: float
    r_terra: Optional[float] = None
    s_terra: Optional[float] = None
    t_terra: Optional[float] = None
    rs: Optional[float] = None
    st: Optional[float] = None
    tr: Optional[float] = None

    def validar(self) -> Dict:
        valores = [self.r_terra, self.s_terra, self.t_terra, self.rs, self.st, self.tr]
        statuses = [status_isolamento(v) for v in valores]
        return {
            "status_r_terra": statuses[0],
            "status_s_terra": statuses[1],
            "status_t_terra": statuses[2],
            "status_rs": statuses[3],
            "status_st": statuses[4],
            "status_tr": statuses[5],
            "status_geral": status_geral(statuses),
        }
