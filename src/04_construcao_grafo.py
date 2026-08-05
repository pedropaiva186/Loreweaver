"""Etapa 4 — Construção do grafo de conhecimento de Hollow Knight."""

import json
import networkx as nx
from util_comum import DIR_DADOS


def carregar_triplas():
    caminho = DIR_DADOS / "triplas_refinadas.json"
    if not caminho.exists():
        raise SystemExit(f"Arquivo não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding='utf-8'))["triplas"]


def construir_grafo(triplas):
    g = nx.MultiDiGraph()
    for n, t in enumerate(triplas):
        origem = str(t["origem"])
        destino = str(t["destino"])
        tipo_origem = str(t.get("tipo_origem") or "?")
        tipo_destino = str(t.get("tipo_destino") or "?")
        relacao = str(t.get("relacao") or "?")
        fonte = str(t.get("fonte") or "?")
        evidencia = str(t.get("evidencia") or "")

    
        if origem not in g or g.nodes[origem].get("tipo") == "?":
            g.add_node(origem, label=origem, tipo=tipo_origem)
            
        if destino not in g or g.nodes[destino].get("tipo") == "?":
            g.add_node(destino, label=destino, tipo=tipo_destino)


        g.add_edge(
            origem,
            destino,
            key=f"e{n}",
            label=relacao,
            relacao=relacao,
            fonte=fonte,
            evidencia=evidencia,
        )
    return g


def main():
    triplas = carregar_triplas()
    g = construir_grafo(triplas)

    print(f"Grafo construído: {g.number_of_nodes()} nós, {g.number_of_edges()} arestas\n")

    por_tipo = {}
    for no, dados in g.nodes(data=True):
        por_tipo.setdefault(dados.get("tipo", "?"), []).append(no)
    for tipo, nos in sorted(por_tipo.items()):
        print(f"  {tipo}: {', '.join(sorted(nos))}")

    print("\nNós mais conectados (grau total):")
    graus = sorted(g.degree(), key=lambda x: -x[1])[:5]
    for no, grau in graus:
        print(f"  {no}: {grau}")

    saida = DIR_DADOS / "grafo.graphml"
    nx.write_graphml(g, saida)
    print(f"\nGrafo salvo em {saida} (abra no yEd/Gephi para visualizar)")


if __name__ == '__main__':
    main()
