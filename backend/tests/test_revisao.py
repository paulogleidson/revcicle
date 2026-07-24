from datetime import date

import pytest

from app.services.revisao import calcular_proxima_revisao

HOJE = date(2026, 7, 23)


class TestCalcularProximaRevisao:
    def test_100_porcento_soma_30_dias(self):
        assert calcular_proxima_revisao(100, HOJE) == date(2026, 8, 22)

    def test_faixa_media_limite_inferior_70_soma_7_dias(self):
        assert calcular_proxima_revisao(70, HOJE) == date(2026, 7, 30)

    def test_faixa_media_limite_superior_99_soma_7_dias(self):
        assert calcular_proxima_revisao(99, HOJE) == date(2026, 7, 30)

    def test_faixa_media_valor_intermediario_85_soma_7_dias(self):
        assert calcular_proxima_revisao(85, HOJE) == date(2026, 7, 30)

    def test_valor_fracionario_dentro_da_faixa_media(self):
        # 99.9 ainda cai em "70 a 99%" (< 100), não em "100%"
        assert calcular_proxima_revisao(99.9, HOJE) == date(2026, 7, 30)

    def test_baixo_desempenho_logo_abaixo_de_70_soma_1_dia(self):
        assert calcular_proxima_revisao(69.99, HOJE) == date(2026, 7, 24)

    def test_baixo_desempenho_zero_soma_1_dia(self):
        assert calcular_proxima_revisao(0, HOJE) == date(2026, 7, 24)

    def test_percentual_negativo_levanta_erro(self):
        with pytest.raises(ValueError):
            calcular_proxima_revisao(-1, HOJE)

    def test_percentual_acima_de_100_levanta_erro(self):
        with pytest.raises(ValueError):
            calcular_proxima_revisao(100.1, HOJE)
