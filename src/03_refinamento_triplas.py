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


#
SINONIMOS_RELACAO = {
    "vence": "derrota",
    "utiliza": "usa",
    "usufrui": "usa",
    "esta_em": "localizado_em",
}

INVERSAS = {
    "e_pai_de": "eh_filho_de",
    "e_mae_de": "eh_filho_de",
}

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
    elif rel in SINONIMOS_RELACAO:
        rel = SINONIMOS_RELACAO[rel]
    tripla["relacao"] = rel
    return tripla


def main():
    entrada = DIR_DADOS / "triplas_brutas.json"
    if not entrada.exists():
        raise SystemExit(f"Arquivo não encontrado: {entrada}")

    triplas = json.loads(entrada.read_text(encoding="utf-8"))["triplas"]

    # 1. Primeira passagem: validação e normalização inicial
    validas = []
    for i, t in enumerate(triplas):
        if not validar_tripla(t):
            print(f"[aviso] tripla inválida no índice {i}; pulando")
            continue
        t["origem"] = normalizar_nome(t["origem"])
        t["destino"] = normalizar_nome(t["destino"])
        normalizar_relacao(t)
        validas.append(t)
    triplas = validas

    # -------------------------------------------------------------------------
    # PONTO DE CHECAGEM: Resolução de Entidades por LLM
    # -------------------------------------------------------------------------
    arquivo_checkpoint = DIR_DADOS / "resolucao_entidades.json"

    if arquivo_checkpoint.exists():
        print(f"  [checkpoint] Carregando mapa de entidades existente em: {arquivo_checkpoint}")
        grupos = json.loads(arquivo_checkpoint.read_text(encoding="utf-8")).get("grupos", [])
    else:
        print("  [LLM] Gerando agrupamento de entidades via modelo...")
        nomes = sorted({t["origem"] for t in triplas} | {t["destino"] for t in triplas})
        prompt = PROMPT_RESOLUCAO.format(nomes="\n".join(f"- {n}" for n in nomes))

        resposta = chamar_modelo(prompt, temperature=0.0)

        # Sanitiza blocos de código Markdown caso o modelo responda com ```json ... ```
        resposta_limpa = re.sub(r"^```(?:json)?\n|```$", "", resposta.strip(), flags=re.IGNORECASE).strip()

        try:
            dados_resposta = json.loads(resposta_limpa)
            grupos = dados_resposta.get("grupos", [])

            # Salva o checkpoint imediatamente após a resposta bem-sucedida do LLM
            escrever_json(arquivo_checkpoint, dados_resposta)
            print(f"  [checkpoint] Salvo com sucesso em: {arquivo_checkpoint}")
        except json.JSONDecodeError as err:
            print(f"  ⚠️ [erro] Falha ao decodificar JSON da LLM: {err}. Prosseguindo sem mapa de aliases.")
            grupos = []

    # Construção do mapa de aliases para canônico
    mapa = {}
    for grupo in grupos:
        canonico = grupo.get("canonico")
        for alias in grupo.get("aliases", []):
            mapa[alias] = canonico

    # 2. Aplicação da resolução de entidades
    for t in triplas:
        t["origem"] = mapa.get(t["origem"], t["origem"])
        t["destino"] = mapa.get(t["destino"], t["destino"])

    # 3. Deduplicação final por chave (origem, relacao, destino)
    vistos = set()
    refinadas = []
    for t in triplas:
        chave = (t["origem"], t["relacao"], t["destino"])
        if chave not in vistos:
            vistos.add(chave)
            refinadas.append(t)

    # Exportação das triplas tratadas
    escrever_json(DIR_DADOS / "triplas_refinadas.json", {"triplas": refinadas})
    print(f"Saída final: {len(refinadas)} triplas refinadas -> {DIR_DADOS / 'triplas_refinadas.json'}")


if __name__ == "__main__":
    main()