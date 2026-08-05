"""Etapa 7 — O mesmo grafo em um banco de grafos: Memgraph + Cypher.

Carrega as triplas refinadas no Memgraph usando Rótulos e Relações Nativas,
executa consultas Cypher e demonstra text-to-Cypher com schema rigoroso.
"""

import json
import sys
import re
from importlib import import_module

import ollama
from neo4j import GraphDatabase

from util_comum import DIR_DADOS, MODEL

mod04 = import_module("04_construcao_grafo")

URI = "bolt://localhost:7687"

# Listas de validação/normalização conforme o seu schema
ENTIDADES_VALIDAS = {
    "item", "local", "npc", "conceito", "inimigo", 
    "habilidade", "chefe", "vendedor", "grupo"
}

RELACOES_VALIDAS = {
    "contem", "derrota", "usa", "localizado_em", "afeta", "requer",
    "executa_habilidade", "leva_a", "vende", "dropa", "libera",
    "cria", "eh_inimigo_de", "eh_relatado_por", "eh_membro_de", "protege"
}

def sanitizar_identificador(texto: str, padrao: str = "OUTRO") -> str:
    """Sanitiza strings para uso seguro como Rótulos ou Tipos de Aresta no Cypher."""
    if not texto:
        return padrao
    limpo = re.sub(r'[^a-zA-Z0-9_]', '_', texto).lower().strip('_')
    return limpo.upper() if limpo else padrao

CONSULTAS_CYPHER = {
    "Chefes derrotados no jogo": """
        MATCH (p)-[r:DERROTA]->(c:CHEFE)
        RETURN DISTINCT p.nome AS heroi, c.nome AS chefe
        LIMIT 15
    """,
    
    "Itens requeridos ou usados": """
        MATCH (item:ITEM)-[r:REQUER|USA]->(destino)
        RETURN DISTINCT item.nome AS item, type(r) AS relacao, destino.nome AS alvo
        LIMIT 10
    """,
    
    "Conexões de Locais": """
        MATCH (origem:LOCAL)-[r:LEVA_A|LOCALIZADO_EM]->(destino:LOCAL)
        RETURN DISTINCT origem.nome AS origem, type(r) AS relacao, destino.nome AS destino
        LIMIT 10
    """,
    
    "Itens vendidos por vendedores": """
        MATCH (v:VENDEDOR)-[r:VENDE]->(item:ITEM)
        RETURN DISTINCT v.nome AS vendedor, item.nome AS item
        LIMIT 10
    """,
}

PROMPT_TEXT2CYPHER = """Você é um especialista em Cypher que gera consultas para Memgraph/Neo4j.

SCHEMA DO BANCO:
- ENTIDADES (Labels dos Nós em MAIÚSCULAS):
  :ITEM, :LOCAL, :NPC, :CONCEITO, :INIMIGO, :HABILIDADE, :CHEFE, :VENDEDOR, :GRUPO

- PROPRIEDADES DOS NÓS:
  {nome: "Nome da Entidade"}

- RELAÇÕES (Tipos de Aresta em MAIÚSCULAS):
  -[:CONTEM]->, -[:DERROTA]->, -[:USA]->, -[:LOCALIZADO_EM]->, -[:AFETA]->,
  -[:REQUER]->, -[:EXECUTA_HABILIDADE]->, -[:LEVA_A]->, -[:VENDE]->, -[:DROPA]->,
  -[:LIBERA]->, -[:CRIA]->, -[:EH_INIMIGO_DE]->, -[:EH_RELATADO_POR]->,
  -[:EH_MEMBRO_DE]->, -[:PROTEGE]->

EXEMPLOS DE CONSULTAS CORRETAS:
1. "O que o vendedor vende?"
   MATCH (v:VENDEDOR)-[:VENDE]->(i:ITEM) RETURN v.nome, i.nome

2. "Quais locais estão contidos em outro?"
   MATCH (l1:LOCAL)-[:LOCALIZADO_EM|CONTEM]->(l2:LOCAL) RETURN l1.nome, l2.nome

REGRAS CRÍTICAS:
- Use Rótulos (:CHEFE, :ITEM) e Tipos de Aresta (-[:DERROTA]->) diretamente na sintaxe do Cypher.
- NUNCA use :ENTIDADE ou :RELACAO genéricos.
- NUNCA crie Rótulos ou Relações fora do schema acima.
- Responda APENAS com o código Cypher puro, sem blocos de markdown e sem explicações.

PERGUNTA: {pergunta}
"""


def carregar_no_memgraph(driver, triplas):
    with driver.session() as sessao:
        sessao.run("MATCH (n) DETACH DELETE n")
        for t in triplas:
            # 1. Normaliza tipos de origem, destino e relação
            raw_origem = t.get("tipo_origem", "conceito").lower()
            raw_destino = t.get("tipo_destino", "conceito").lower()
            raw_rel = t.get("relacao", "afeta").lower()

            # Valida contra o schema (fallback para CONCEITO / AFETA se inválido)
            label_origem = sanitizar_identificador(raw_origem if raw_origem in ENTIDADES_VALIDAS else "conceito")
            label_destino = sanitizar_identificador(raw_destino if raw_destino in ENTIDADES_VALIDAS else "conceito")
            tipo_relacao = sanitizar_identificador(raw_rel if raw_rel in RELACOES_VALIDAS else "afeta")

            # 2. Insere usando Rótulos e Relação Nativos
            query = f"""
            MERGE (a:`{label_origem}` {{nome: $origem}})
            MERGE (b:`{label_destino}` {{nome: $destino}})
            MERGE (a)-[r:`{tipo_relacao}`]->(b)
            SET r.fonte = $fonte, r.evidencia = $evidencia
            """

            sessao.run(
                query,
                origem=t["origem"],
                destino=t["destino"],
                fonte=t.get("fonte", "?"),
                evidencia=t.get("evidencia", ""),
            )

        total = sessao.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        rels = sessao.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
    print(f"Memgraph carregado: {total} nós, {rels} relações com Rótulos Nativos!")


def executar(driver, cypher):
    with driver.session() as sessao:
        return [dict(reg) for reg in sessao.run(cypher)]


def gerar_cypher_com_llm(pergunta):
    response = ollama.chat(
        model=MODEL,
        format="",
        messages=[{"role": "user", "content": PROMPT_TEXT2CYPHER.format(pergunta=pergunta)}],
        options={"temperature": 0.0, "num_ctx": 32768, "num_predict": 1024},
    )
    cypher = response["message"]["content"].strip()
    cypher = re.sub(r"^```(?:cypher)?\n|```$", "", cypher, flags=re.IGNORECASE).strip()
    return cypher


def main():
    triplas = mod04.carregar_triplas()
    try:
        driver = GraphDatabase.driver(URI, auth=("", ""))
        driver.verify_connectivity()
    except Exception as erro:
        raise SystemExit(
            f"Não foi possível conectar ao Memgraph em {URI} ({erro}).\n"
            "Suba o container: docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph-mage"
        )

    carregar_no_memgraph(driver, triplas)

    print("=" * 80)
    print("🎮 EXPLORADOR DA LORE — HOLLOW KNIGHT (CYPHER NATIVO) 🎮")
    print("=" * 80)

    for titulo, cypher in CONSULTAS_CYPHER.items():
        print(f"\n{titulo}")
        print("-" * 80)
        try:
            resultados = executar(driver, cypher)
            if resultados:
                for linha in resultados:
                    print(f"  ✓ {linha}")
            else:
                print("  (sem resultados)")
        except Exception as e:
            print(f"Erro na consulta: {e}")

    if "--llm" in sys.argv:
        perguntas = [
            "Quais itens o vendedor vende?",
            "Qual habilidade afeta ou derrota o chefe?",
            "Quais inimigos estão em qual local?"
        ]
        
        print("\n" + "=" * 80)
        print("CONSULTAS GERADAS POR IA (text-to-Cypher)")
        print("=" * 80)
        
        for pergunta in perguntas:
            print(f"\n[❓] {pergunta}")
            try:
                cypher = gerar_cypher_com_llm(pergunta)
                print(f"Cypher gerado: {cypher}")
                resultados = executar(driver, cypher)
                for linha in resultados:
                    print(f"  → {linha}")
            except Exception as erro:
                print(f"Consulta falhou: {erro}")

    driver.close()
    print("\nExploração da lore concluída!")

if __name__ == "__main__":
    main()