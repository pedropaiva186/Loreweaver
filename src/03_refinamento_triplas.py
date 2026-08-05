"""Etapa 3 — Refinamento e normalização do grafo de Hollow Knight."""

import json
import re
import unicodedata
from pathlib import Path
from util_comum import chamar_modelo, escrever_json, DIR_DADOS

REQUIRED_TRIPLA_KEYS = {"origem", "tipo_origem", "destino", "tipo_destino", "relacao", "fonte"}

def validar_tripla(tripla):
    if not isinstance(tripla, dict):
        return False
    return REQUIRED_TRIPLA_KEYS.issubset(tripla.keys())


def remover_acentos(texto):
    texto = str(texto)
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))




SINONIMOS_RELACAO = {
    "contem": None,
    "derrota": "vence",
    "usa": {"utiliza", "usufrui"},
    "afeta": none,
    "e_parte_de": "esta_em",
} # A decidir

  - usa
  - localizado_em
  - afeta
  - requer
  - executa_habilidade
  - leva_a
  - vende
  - dropa
  - libera
  - cria
  - eh_inimigo_de
  - eh_relatado_por
  - eh_membro_de
  - protege

INVERSAS = {
    "e_pai_de": "e_filho_de",
    "e_mae_de": "e_filho_de",
    "e_irmao_de": "e_irmao_de",
} # A decidir

PROMPT_RESOLUCAO = '''A lista abaixo contém nomes de entidades extraídos do universo Hollow Knight.
Alguns nomes diferentes podem se referir à MESMA entidade (aliases, tradução, variação de grafia).
Agrupe os aliases e responda apenas com JSON no formato:
{{"grupos": [{{"canonico": "Nome Canônico", "aliases": ["variação 1", "variação 2"]}}]}}

Inclua um grupo apenas quando houver mais de uma grafia para a mesma entidade.
NOMES:
{nomes}'''


def normalizar_nome(nome):
    n = " ".join(str(nome).split())
    n = re.sub(r"^o |^a |^os |^as ", "", n, flags=re.IGNORECASE)
    n = remover_acentos(n)
    return n.strip()


def normalizar_relacao(tripla):
    rel = remover_acentos(tripla["relacao"].lower()).replace(" ", "_")
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

    validas = []
    for i, t in enumerate(triplas):
        if not validar_tripla(t):
            print(f"[aviso] tripla inválida no índice {i}: chaves faltando ou formato incorreto; pulando")
            continue
        t["origem"] = normalizar_nome(t["origem"])
        t["destino"] = normalizar_nome(t["destino"])
        normalizar_relacao(t)
        validas.append(t)
    triplas = validas

    nomes = sorted({t["origem"] for t in triplas} | {t["destino"] for t in triplas})
    prompt = PROMPT_RESOLUCAO.format(nomes="\n".join(f"- {n}" for n in nomes))
    resposta = chamar_modelo(prompt, temperature=0.0)

    grupos = json.loads(resposta).get("grupos", [])
    mapa = {}
    for grupo in grupos:
        for alias in grupo.get("aliases", []):
            mapa[alias] = grupo["canonico"]

    for t in triplas:
        if not validar_tripla(t):
            continue
        t["origem"] = mapa.get(t["origem"], t["origem"])
        t["destino"] = mapa.get(t["destino"], t["destino"])

    vistos = set()
    refinadas = []
    for t in triplas:
        if not validar_tripla(t):
            continue
        chave = (t["origem"], t["relacao"], t["destino"])
        if chave not in vistos:
            vistos.add(chave)
            refinadas.append(t)

    escrever_json(DIR_DADOS / "triplas_refinadas.json", {"triplas": refinadas})
    print(f"Saída: {len(refinadas)} triplas refinadas -> {DIR_DADOS / 'triplas_refinadas.json'}")


if __name__ == '__main__':
    main()
