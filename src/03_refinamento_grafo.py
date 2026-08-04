"""Etapa 3 — Refinamento e normalização do grafo de Hollow Knight."""

import json
from pathlib import Path
import re
from .util_comum import chamar_modelo, escrever_json, DIR_DADOS

SINONIMOS_RELACAO = {
    "e_pai_de": None,
    "e_mae_de": None,
    "e_irmao_de": None,
    "tem_item": "possui_item",
    "e_parte_de": "esta_em",
} # A decidir

INVERSAS = {
    "e_pai_de": "e_filho_de",
    "e_mae_de": "e_filho_de",
    "e_irmao_de": "e_irmao_de",
} # A decidir

PROMPT_RESOLUCAO = '''A lista abaixo contém nomes de entidades extraídos do universo Hollow Knight.
Alguns nomes diferentes podem se referir à MESMA entidade (aliases, tradução, variação de grafia).
Agrupe os aliases e responda apenas com JSON no formato:
{"grupos": [{"canonico": "Nome Canônico", "aliases": ["variação 1", "variação 2"]}]}

Inclua um grupo apenas quando houver mais de uma grafia para a mesma entidade.
NOMES:
{nomes}'''


def normalizar_nome(nome):
    n = " ".join(str(nome).split())
    n = re.sub(r"^o |^a |^os |^as ", "", n, flags=re.IGNORECASE)
    return n.strip()


def normalizar_relacao(tripla):
    rel = tripla["relacao"].lower().replace(" ", "_")
    if rel in INVERSAS:
        tripla["origem"], tripla["destino"] = tripla["destino"], tripla["origem"]
        rel = INVERSAS[rel]
    elif rel in SINONIMOS_RELACAO and SINONIMOS_RELACAO[rel] is not None:
        rel = SINONIMOS_RELACAO[rel]
    tripla["relacao"] = rel
    return tripla


def main():
    entrada = DIR_DADOS / "triplas_brutas.json"
    if not entrada.exists():
        raise SystemExit(f"Arquivo não encontrado: {entrada}")
    triplas = json.loads(entrada.read_text(encoding='utf-8'))["triplas"]

    for t in triplas:
        t["origem"] = normalizar_nome(t["origem"])
        t["destino"] = normalizar_nome(t["destino"])
        normalizar_relacao(t)

    nomes = sorted({t["origem"] for t in triplas} | {t["destino"] for t in triplas})
    prompt = PROMPT_RESOLUCAO.format(nomes="\n".join(f"- {n}" for n in nomes))
    resposta = chamar_modelo(prompt, temperature=0.0)

    grupos = json.loads(resposta).get("grupos", [])
    mapa = {}
    for grupo in grupos:
        for alias in grupo.get("aliases", []):
            mapa[alias] = grupo["canonico"]

    for t in triplas:
        t["origem"] = mapa.get(t["origem"], t["origem"])
        t["destino"] = mapa.get(t["destino"], t["destino"])

    vistos = set()
    refinadas = []
    for t in triplas:
        chave = (t["origem"], t["relacao"], t["destino"])
        if chave not in vistos:
            vistos.add(chave)
            refinadas.append(t)

    escrever_json(DIR_DADOS / "triplas_refinadas.json", {"triplas": refinadas})
    print(f"Saída: {len(refinadas)} triplas refinadas -> {DIR_DADOS / 'triplas_refinadas.json'}")


if __name__ == '__main__':
    main()
