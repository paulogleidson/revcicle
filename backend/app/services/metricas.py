from collections import defaultdict
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SessaoComConteudo:
    sessao_id: int
    conteudo_id: int
    titulo: str
    materia: str
    data: date
    percentual: float
    proxima_revisao: date


def agregar_metricas(sessoes: list[SessaoComConteudo]) -> dict:
    """Monta as três agregações da tela de desempenho a partir das sessões de um usuário.

    - evolucao: série de (data, percentual) por conteúdo, em ordem cronológica;
    - por_materia: média de acerto e total de revisões por matéria, maior média primeiro;
    - calendario: por dia, as revisões realizadas e a próxima revisão agendada de cada
      conteúdo (só a da última sessão, que é a que vale para o Dashboard).
    """
    ordenadas = sorted(sessoes, key=lambda s: (s.data, s.sessao_id))

    evolucao: dict[int, dict] = {}
    for s in ordenadas:
        serie = evolucao.setdefault(
            s.conteudo_id,
            {"conteudo_id": s.conteudo_id, "titulo": s.titulo, "materia": s.materia, "pontos": []},
        )
        serie["pontos"].append({"data": s.data, "percentual": s.percentual})

    soma_por_materia: dict[str, list[float]] = defaultdict(list)
    for s in ordenadas:
        soma_por_materia[s.materia].append(s.percentual)
    por_materia = [
        {
            "materia": materia,
            "media_percentual": round(sum(valores) / len(valores), 1),
            "total_revisoes": len(valores),
        }
        for materia, valores in soma_por_materia.items()
    ]
    por_materia.sort(key=lambda m: (-m["media_percentual"], m["materia"]))

    dias: dict[date, dict] = {}

    def dia(d: date) -> dict:
        return dias.setdefault(d, {"data": d, "realizadas": [], "agendadas": []})

    ultima_por_conteudo: dict[int, SessaoComConteudo] = {}
    for s in ordenadas:
        dia(s.data)["realizadas"].append(
            {"conteudo_id": s.conteudo_id, "titulo": s.titulo, "percentual": s.percentual}
        )
        atual = ultima_por_conteudo.get(s.conteudo_id)
        if atual is None or s.sessao_id > atual.sessao_id:
            ultima_por_conteudo[s.conteudo_id] = s
    for s in ultima_por_conteudo.values():
        dia(s.proxima_revisao)["agendadas"].append(
            {"conteudo_id": s.conteudo_id, "titulo": s.titulo, "percentual": None}
        )

    return {
        "evolucao": list(evolucao.values()),
        "por_materia": por_materia,
        "calendario": [dias[d] for d in sorted(dias)],
    }
