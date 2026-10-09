import json
import math
import unittest

import models


META = {"usina": "Usina Teste", "tag": "EQ-01"}


class CalculosCompartilhadosTest(unittest.TestCase):
    def test_relacao_teorica_considera_ligacoes(self):
        casos = [
            ("DELTA", "DELTA", 17.25),
            ("ESTRELA", "ESTRELA", 17.25),
            ("DELTA", "ESTRELA", 17.25 * math.sqrt(3)),
            ("ESTRELA", "DELTA", 17.25 / math.sqrt(3)),
        ]
        for at, bt, esperado in casos:
            with self.subTest(at=at, bt=bt):
                obtido = models.relacao_teorica_trafo(13800, 800, at, bt)
                self.assertAlmostEqual(obtido, esperado, places=9)

    def test_relacao_teorica_rejeita_dados_inconsistentes(self):
        self.assertIsNone(models.relacao_teorica_trafo(13800, 0, "DELTA", "ESTRELA"))
        self.assertIsNone(models.relacao_teorica_trafo(13800, 800, None, "ESTRELA"))
        self.assertIsNone(models.erro_relativo(10, 0))

    def test_status_geral_mantem_prioridade_existente(self):
        self.assertEqual(
            models.status_geral([models.STATUS_CONFORME, models.STATUS_RESSALVA]),
            models.STATUS_RESSALVA,
        )
        self.assertEqual(
            models.status_geral([models.STATUS_RESSALVA, models.STATUS_ATENCAO]),
            models.STATUS_ATENCAO,
        )


class TransformadorTest(unittest.TestCase):
    def test_ttr_e_ohmica_retornam_detalhes_por_fase(self):
        referencia = models.relacao_teorica_trafo(13800, 800, "DELTA", "ESTRELA")
        resultado = models.EnsaioTrafo(
            **META,
            tipo="TRAFO",
            nom_pri=13800,
            nom_sec=800,
            rn_teorico=17.25,  # valor legado incorreto deve ser ignorado
            ligacao_at="DELTA",
            ligacao_bt="ESTRELA",
            ttr_a=referencia,
            ttr_b=referencia * 1.004,
            ttr_c=referencia * 0.996,
            h1=100,
            h2=102,
            h3=98,
            x1=10,
            x2=10,
            x3=10,
        ).validar()

        self.assertAlmostEqual(resultado["rn_teorico"], referencia, places=6)
        self.assertEqual(resultado["status_ttr"], models.STATUS_CONFORME)
        self.assertEqual(resultado["media_h"], 100)
        self.assertEqual(resultado["desvios_h_pct"], [0.0, 2.0, 2.0])
        self.assertEqual(resultado["status_h"], models.STATUS_CONFORME)
        self.assertEqual(resultado["status_x"], models.STATUS_CONFORME)

    def test_ohmica_incompleta_nao_e_avaliada(self):
        resultado = models.EnsaioTrafo(
            **META,
            tipo="TRAFO",
            ligacao_at="DELTA",
            ligacao_bt="DELTA",
            h1=100,
            h2=101,
        ).validar()
        self.assertEqual(resultado["status_h"], models.STATUS_NAO_AVALIADO)
        self.assertIsNone(resultado["media_h"])
        self.assertEqual(resultado["desvios_h_pct"], [None, None, None])

    def test_tp_tc_recalcula_relacao_no_backend(self):
        secundarios = [{
            "nominal_secundario": 115,
            "rn_teorico": 999,
            "relacao_medida": 120,
            "tolerancia_pct": 1,
            "riso_prim_sec": 1000,
            "riso_sec_terra": 1000,
        }]
        resultado = models.EnsaioTrafo(
            **META,
            tipo="TP",
            nom_pri=13800,
            secundarios_json=json.dumps(secundarios),
            at_t=1000,
        ).validar()
        self.assertEqual(resultado["rn_teorico"], 120.0)
        self.assertEqual(resultado["erro_ttr_a_pct"], 0.0)
        self.assertEqual(resultado["status_ttr"], models.STATUS_CONFORME)


class DemaisEnsaiosTest(unittest.TestCase):
    def test_resistencia_de_aterramento(self):
        conforme = models.EnsaioResMalha(
            **META, d_total=30, r52=5.1, r62=5, r72=4.9
        ).validar()
        self.assertEqual(conforme["status_patamar"], models.STATUS_CONFORME)
        self.assertEqual(conforme["status_valor"], models.STATUS_CONFORME)

        refazer = models.EnsaioResMalha(
            **META, d_total=30, r52=4, r62=5, r72=6
        ).validar()
        self.assertEqual(refazer["status_geral"], models.STATUS_REFAZER)
        self.assertEqual(refazer["status_valor"], models.STATUS_NAO_AVALIADO)

    def test_manobra_limite_e_desequilibrio(self):
        por_valor = models.EnsaioManobra(
            **META, res_c_r=301, res_c_s=300, res_c_t=299
        ).validar(models.LIMITE_CONTATO_MT_UOHM)
        self.assertEqual(por_valor["status_contato"], models.STATUS_ATENCAO)

        por_desequilibrio = models.EnsaioManobra(
            **META, res_c_r=100, res_c_s=111, res_c_t=100
        ).validar(models.LIMITE_CONTATO_MT_UOHM)
        self.assertEqual(por_desequilibrio["status_contato"], models.STATUS_ATENCAO)

    def test_strings_cc_e_isolamento(self):
        resultado = models.EnsaioCabosCC(
            **META,
            voc=1000,
            v_pos_terra=100,
            v_neg_terra=50,
            n_modulos=20,
            voc_stc=50,
            beta_voc=0,
            temperatura_modulo=25,
        ).validar()
        self.assertEqual(resultado["status_voc"], models.STATUS_CONFORME)
        self.assertEqual(resultado["status_diagnostico"], models.STATUS_CONFORME)
        self.assertEqual(models.status_isolamento(999.9), models.STATUS_RESSALVA)
        self.assertEqual(models.status_isolamento(1000), models.STATUS_CONFORME)


if __name__ == "__main__":
    unittest.main()
