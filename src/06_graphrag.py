"""Etapa 6 — Consulta GraphRAG no grafo de Hollow Knight."""

import difflib
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path
import networkx as nx

from util_comum import chamar_modelo, chamar_modelo_sem_json, DIR_DADOS

BASE_DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "construcao_grafo", BASE_DIR / "04_construcao_grafo.py"
)
mod04 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod04)

PERGUNTAS_PADRAO = [
    "Quais personagens ou chefes estão localizados em Hallownest?",
    "Quem derrotou o Lorde Traidor (Traitor Lord) e onde ele aparece?",
    "Qual a relação entre Hornet e o Cavaleiro (Knight)?",
]

K_SALTOS = 1  # Reduzido para 1 salto para focar no contexto direto e evitar ruído
MAX_ARESTAS_CONTEXTO = 150  # Limite máximo para não poluir o prompt


def normalizar_texto(texto: str) -> str:
    """Remove acentos e força minúsculas para facilitar o matching."""
    texto = str(texto).lower().strip()
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def extrair_entidades_da_pergunta(pergunta):
    prompt = (
        "Liste as entidades nomeadas (personagens, locais, chefes, objetos) mencionadas na pergunta.\n"
        "Responda APENAS com um JSON no formato: {\"entidades\": [\"nome1\", \"nome2\"]}\n\n"
        f"PERGUNTA: {pergunta}"
    )
    resposta = chamar_modelo(prompt, temperature=0.0)
    
    # Sanitização contra blocos Markdown
    resposta_limpa = re.sub(r"^```(?:json)?\n|```$", "", resposta.strip(), flags=re.IGNORECASE).strip()
    
    try:
        return json.loads(resposta_limpa).get("entidades", [])
    except json.JSONDecodeError:
        return []


def casar_com_nos(entidades, g):
    """Matching híbrido: similaridade difusa + busca por substring normalizada."""
    nos_originais = list(g.nodes)
    nos_norm = {normalizar_texto(n): n for n in nos_originais}
    ancoras = set()

    for e in entidades:
        e_norm = normalizar_texto(e)
        if not e_norm:
            continue

        # 1. Busca Exata Normalizada
        if e_norm in nos_norm:
            ancoras.add(nos_norm[e_norm])
            continue

        # 2. Busca por Contenção (Substring)
        candidatos_sub = [no_orig for no_norm, no_orig in nos_norm.items() if e_norm in no_norm or no_norm in e_norm]
        if candidatos_sub:
            ancoras.add(candidatos_sub[0])
            continue

        # 3. Match Difuso (difflib) como fallback
        matches = difflib.get_close_matches(e_norm, list(nos_norm.keys()), n=1, cutoff=0.5)
        if matches:
            ancoras.add(nos_norm[matches[0]])

    return list(ancoras)


def expandir_subgrafo(g, ancoras, k=K_SALTOS):
    """Extrai o subgrafo unindo a vizinhança direta dos nós-âncora."""
    g_nd = g.to_undirected()
    nos = set()
    
    for a in ancoras:
        if a in g_nd:
            nos |= set(nx.ego_graph(g_nd, a, radius=k).nodes)
            
    return g.subgraph(nos)


def serializar_subgrafo(sub, max_arestas=MAX_ARESTAS_CONTEXTO):
    """Serializa as arestas em texto legível, limitando a quantidade para economizar contexto."""
    linhas = []
    arestas = list(sub.edges(data=True))[:max_arestas]
    
    for u, v, dados in arestas:
        rel = dados.get("relacao", "relacionado_a")
        linha = f"({u}) -[{rel}]-> ({v})"
        
        if dados.get("evidencia"):
            linha += f'   [evidência: "{dados["evidencia"]}" — {dados.get("fonte", "?")}]'
            
        linhas.append(linha)
        
    return "\n".join(sorted(linhas))


def responder(pergunta, contexto_grafo):
    prompt = (
        "Você é um especialista no universo de Hollow Knight. Responda à pergunta "
        "com base EXCLUSIVAMENTE no subgrafo de conhecimento fornecido abaixo.\n"
        "Se o contexto não contiver informação suficiente, informe o que foi encontrado e o que falta.\n"
        "Ao final da resposta, OBRIGATORIAMENTE liste as relações que você utilizou para construir seu raciocínio: no formato: (origem) -[relação]-> (destino) \n\n"
        f"CONTEXTO (Subgrafo de Triplas):\n{contexto_grafo}\n\n"
        f"PERGUNTA: {pergunta}"
    )
    return chamar_modelo_sem_json(prompt, temperature=0.0)


def main():
    g = mod04.construir_grafo(mod04.carregar_triplas())
    perguntas = [" ".join(sys.argv[1:])] if len(sys.argv) > 1 and sys.argv[1] else PERGUNTAS_PADRAO

    for i, pergunta in enumerate(perguntas):
        if i > 0:
            try:
                input("\n[Pressione Enter para a próxima pergunta...]")
            except EOFError:
                pass
                
        print("\n" + "=" * 72)
        print(f"PERGUNTA: {pergunta}")

        entidades = extrair_entidades_da_pergunta(pergunta)
        ancoras = casar_com_nos(entidades, g)
        print(f"Entidades extraídas: {entidades}")
        print(f"Nós-âncora mapeados no Grafo: {ancoras}")

        if not ancoras:
            print("Nenhum nó correspondente encontrado no grafo.")
            continue

        sub = expandir_subgrafo(g, ancoras)
        print(f"Subgrafo recuperado: {sub.number_of_nodes()} nós, {sub.number_of_edges()} arestas")

        contexto = serializar_subgrafo(sub)
        
        if not contexto:
            print("Subgrafo isolado (sem arestas para formar contexto).")
            continue

        resposta = responder(pergunta, contexto)
        print(f"\nRESPOSTA (GraphRAG):\n{resposta}")


if __name__ == "__main__":
    main()