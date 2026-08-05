"""Etapa 6 — Consulta GraphRAG no grafo de Hollow Knight."""

import difflib
import importlib.util
import json
import sys
from pathlib import Path
import networkx as nx
from util_comum import chamar_modelo, DIR_DADOS

BASE_DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "construcao_grafo", BASE_DIR / "04_construcao_grafo.py"
)
mod04 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod04)

PERGUNTAS_PADRAO = [
    "Quais personagens foram criados por antigos guardiões em Hallownest?",
    "Qual região de Hollow Knight está associada ao Castelo da Névoa?",
    "Quem derrotou o Traitor Lord e onde ele aparece?",
]

K_SALTOS = 2


def extrair_entidades_da_pergunta(pergunta):
    prompt = (
        "Liste as entidades nomeadas mencionadas nesta pergunta em português. "
        "Responda APENAS com JSON: {\"entidades\": [\"...\", ...]}\n\n"
        f"PERGUNTA: {pergunta}"
    )
    resposta = chamar_modelo(prompt, temperature=0.0)
    return json.loads(resposta)["entidades"]


def casar_com_nos(entidades, g):
    nos = list(g.nodes)
    ancoras = []
    for e in entidades:
        candidatos = difflib.get_close_matches(e, nos, n=1, cutoff=0.6)
        if candidatos:
            ancoras.append(candidatos[0])
    return ancoras


def expandir_subgrafo(g, ancoras, k=K_SALTOS):
    g_nd = g.to_undirected()
    nos = set()
    for a in ancoras:
        nos |= set(nx.ego_graph(g_nd, a, radius=k).nodes)
    return g.subgraph(nos)


def serializar_subgrafo(sub):
    linhas = []
    for u, v, dados in sub.edges(data=True):
        linha = f"({u}) -[{dados['relacao']}]-> ({v})"
        if dados.get("evidencia"):
            linha += f'   [evidência: "{dados["evidencia"]}" — {dados.get("fonte", "?")}]'
        linhas.append(linha)
    return "\n".join(sorted(linhas))


def responder(pergunta, contexto_grafo):
    prompt = (
        "Você é um assistente que responde usando apenas o contexto de um grafo de conhecimento. "
        "O contexto abaixo descreve relações no formato (origem) -[RELACAO]-> (destino).\n"
        "Responda à pergunta com base apenas nessas relações e cite as relações usadas.\n\n"
        f"CONTEXTO:\n{contexto_grafo}\n\nPERGUNTA: {pergunta}"
    )
    return chamar_modelo(prompt, temperature=0.0)


def main():
    g = mod04.construir_grafo(mod04.carregar_triplas())
    perguntas = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 else PERGUNTAS_PADRAO

    for i, pergunta in enumerate(perguntas):
        if i > 0:
            try:
                input("\n[Enter] para a próxima pergunta... ")
            except EOFError:
                pass
        print("\n" + "=" * 72)
        print(f"PERGUNTA: {pergunta}")

        entidades = extrair_entidades_da_pergunta(pergunta)
        ancoras = casar_com_nos(entidades, g)
        print(f"Entidades identificadas: {entidades} -> nós-âncora: {ancoras}")

        if not ancoras:
            print("Nenhuma âncora no grafo; fallback necessário.")
            continue

        sub = expandir_subgrafo(g, ancoras)
        print(f"Subgrafo recuperado: {sub.number_of_nodes()} nós, {sub.number_of_edges()} arestas")

        contexto = serializar_subgrafo(sub)
        print(f"\nRESPOSTA (GraphRAG):\n{responder(pergunta, contexto)}")


if __name__ == '__main__':
    main()
