from datetime import date, timedelta


def calcular_proxima_revisao(percentual: float, data_atual: date) -> date:
    """Calcula a próxima data de revisão a partir do desempenho.

    Regra (CLAUDE.md):
      - 100%          → +30 dias
      - 70% a 99%     → +7 dias
      - menos de 70%  → +1 dia
    """
    if not 0 <= percentual <= 100:
        raise ValueError("percentual deve estar entre 0 e 100")

    if percentual == 100:
        dias = 30
    elif percentual >= 70:
        dias = 7
    else:
        dias = 1

    return data_atual + timedelta(days=dias)
