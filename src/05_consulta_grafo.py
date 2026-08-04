"""Etapa 5 — Consultas de grafo síncronas no domínio Hollow Knight."""

import importlib.util
from pathlib import Path
import networkx as nx

BASE_DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "construcao_grafo", BASE_DIR / "04_construcao_grafo.py"
)
mod04 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod04)


def arestas_com_relacao(g, relacao):
    for u, v, dados in g.edges(data=True):
        if dados["relacao"] == relacao:
            yield u, v, dados


def consulta_multihop_herois(g, personagem):
    print(f"\n[Consulta 1 — multi-hop] Relações envolvendo {personagem}:")
    fundadores = [u for u, v, _ in arestas_com_relacao(g, "derrotou") if v == personagem]
    for fundador in fundadores:
        print(f"  {fundador} derrotou {personagem}")


def consulta_conector_de_locais(g, local_a, local_b):
    print(f"\n[Consulta 2 — agregação] Entidades que conectam {local_a} e {local_b}:")
    g_nd = g.to_undirected()
    for no in g.nodes:
        vizinhos = set(g_nd.neighbors(no))
        if local_a in vizinhos and local_b in vizinhos:
            print(f"  {no} conecta {local_a} e {local_b}")


def consulta_caminho(g, origem, destino):
    print(f"\n[Consulta 3 — caminho] Como '{origem}' se conecta a '{destino}'?")
    try:
        caminho = nx.shortest_path(g.to_undirected(), origem, destino)
    except nx.NetworkXNoPath:
        print("  Sem caminho.")
        return
    for a, b in zip(caminho, caminho[1:]):
        dados = g.get_edge_data(a, b) or g.get_edge_data(b, a)
        relacao = list(dados.values())[0]["relacao"]
        seta = "->" if g.get_edge_data(a, b) else "<-"
        print(f"  {a} {seta}[{relacao}]{seta} {b}")


def main():
    g = mod04.construir_grafo(mod04.carregar_triplas())
    print(f"Grafo: {g.number_of_nodes()} nós, {g.number_of_edges()} arestas")

    consulta_multihop_herois(g, "The Knight")
    consulta_conector_de_locais(g, "Hallownest", "Cidade da Névoa")
    consulta_caminho(g, "Hornet", "Hollow Knight")


if __name__ == '__main__':
    main()
