"""Regras puras da comunidade (sem banco), testáveis isoladamente."""
import unicodedata
from collections.abc import Iterable


def normalizar_materia(materia: str) -> str:
    """Chave de comparação: sem acento, sem caixa e com espaços colapsados.

    `materia` é texto livre, então "Matemática", "matematica " e
    "MATEMÁTICA" precisam contar como a mesma disciplina.
    """
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", materia) if unicodedata.category(c) != "Mn"
    )
    return " ".join(sem_acento.casefold().split())


def disciplinas_em_comum(minhas: Iterable[str], dele: Iterable[str]) -> list[str]:
    """Matérias presentes nas duas listas, com a grafia de quem está vendo.

    Ordem alfabética pela chave normalizada; sem duplicatas.
    """
    chaves_dele = {normalizar_materia(m) for m in dele}
    em_comum: dict[str, str] = {}
    for materia in minhas:
        chave = normalizar_materia(materia)
        if chave and chave in chaves_dele and chave not in em_comum:
            em_comum[chave] = materia.strip()
    return [em_comum[c] for c in sorted(em_comum)]
