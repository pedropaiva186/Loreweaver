"""Etapa 7 (opcional) — O mesmo grafo em um banco de grafos: Memgraph + Cypher.

O NetworkX é ótimo para entender o mecanismo, mas em produção o grafo mora
em um banco de grafos. Este script:
  1. Carrega as triplas refinadas no Memgraph (protocolo Bolt, driver neo4j)
  2. Executa as consultas da etapa 5 reescritas em Cypher
  3. Demonstra text-to-Cypher: o LLM traduz a pergunta em linguagem natural
     para uma consulta Cypher, que é executada no banco

Pré-requisito (Docker):
    docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph-mage

Uso:
    python src/07_memgraph_cypher.py            # carga + consultas fixas
    python src/07_memgraph_cypher.py --llm      # inclui text-to-Cypher
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

CONSULTAS_CYPHER = {
    "Chefes derrotados pelo Cavaleiro": """
        MATCH (cavaleiro:ENTIDADE {nome: 'Cavaleiro'})-[r:RELACAO]->(chefe:ENTIDADE)
        WHERE r.tipo IN ['derrota', 'luta_contra', 'combate_contra']
        RETURN DISTINCT cavaleiro.nome AS heroi, chefe.nome AS chefe
        LIMIT 15
    """,
    
    "Itens necessários para derrotar a Radiância": """
        MATCH (item:ENTIDADE {tipo: 'item'})-[r:RELACAO]->(radiancia:ENTIDADE {nome: 'Radiancia'})
        WHERE r.tipo IN ['requer', 'necessario_para', 'usa']
        RETURN DISTINCT item.nome AS item
        LIMIT 10
    """,
    
    "Locais conectados ao Cavaleiro": """
        MATCH (cavaleiro:ENTIDADE {nome: 'Cavaleiro'})-[r:RELACAO]->(local:ENTIDADE {tipo: 'local'})
        WHERE r.tipo IN ['localizado_em', 'leva_a', 'acesso_a']
        RETURN DISTINCT cavaleiro.nome AS personagem, local.nome AS local
        LIMIT 10
    """,
    
    "Relações familiares de Hornet": """
        MATCH (hornet:ENTIDADE {nome: 'Hornet'})-[r:RELACAO]->(familiar:ENTIDADE)
        WHERE r.tipo IN ['filho', 'filha', 'irma', 'irmao', 'criada_por', 'treinada_por']
        RETURN DISTINCT hornet.nome AS personagem, r.tipo AS tipo_relacao, familiar.nome AS familiar
        LIMIT 10
    """,
}

PROMPT_TEXT2CYPHER = """Você é um especialista em Cypher que conhece EXATAMENTE este schema:

SCHEMA RIGOROSO:
- TODOS os nós têm label :ENTIDADE (sem exceção!)
- TODOS os nós têm propriedades: nome (string), tipo (string)
- TODOS têm uma relação :RELACAO com propriedades: tipo (string), fonte (string), evidencia (string)

TIPOS CANÔNICOS DE NÓ (propriedade 'tipo'):
  item, local, npc, conceito, inimigo, chefe, vendedor, grupo, habilidade, personagem, evento

RELAÇÕES CANÔNICAS (propriedade 'tipo' da relação):
  contem, derrota, usa, localizado_em, afeta, requer, executa_habilidade, leva_a, 
  vende, dropa, libera, cria, eh_inimigo_de, eh_relatado_por, eh_membro_de, protege, 
  filha_de, filho_de, irma, irmao, criada_por, treinada_por, luta_contra, combate_contra

PADRÃO DE CONSULTA (SEMPRE use este padrão):
  MATCH (origem:ENTIDADE {{nome: "Origem", tipo: "tipo1"}})-[r:RELACAO]-(destino:ENTIDADE {{tipo: "tipo2"}})
  WHERE r.tipo = "relacao_especifica"
  RETURN DISTINCT origem.nome, destino.nome, r.tipo

EXEMPLOS CORRETOS:
1. Mãe do Cavaleiro:
   MATCH (cav:ENTIDADE {{nome: "Cavaleiro"}})-[r:RELACAO]-(mae:ENTIDADE)
   WHERE r.tipo IN ["filha_de", "filho_de"]
   RETURN DISTINCT mae.nome

2. Itens para derrotar Radiância:
   MATCH (item:ENTIDADE {{tipo: "item"}})-[r:RELACAO]-(rad:ENTIDADE {{nome: "Radiancia"}})
   WHERE r.tipo = "requer"
   RETURN DISTINCT item.nome

REGRAS CRÍTICAS:
- Use SEMPRE :ENTIDADE, NUNCA :ITEM, :CHEFE, :NPC, etc
- Use SEMPRE {{nome: "..."}} para nomes específicos
- Use SEMPRE {{tipo: "..."}} para filtros de tipo
- Se não sabe o nome exato, use apenas tipo
- Relações SEMPRE têm label :RELACAO
- Responda APENAS com a query Cypher, sem markdown, sem explicações

PERGUNTA: {pergunta}
"""


def carregar_no_memgraph(driver, triplas):
    with driver.session() as sessao:
        sessao.run("MATCH (n) DETACH DELETE n")
        for t in triplas:
            sessao.run(
                """
                MERGE (a:ENTIDADE {nome: $origem, tipo: $tipo_origem})
                MERGE (b:ENTIDADE {nome: $destino, tipo: $tipo_destino})
                MERGE (a)-[r:RELACAO {tipo: $relacao}]->(b)
                SET r.fonte = $fonte, r.evidencia = $evidencia
                """,
                origem=t["origem"],
                tipo_origem=t.get("tipo_origem", "entidade"),
                destino=t["destino"],
                tipo_destino=t.get("tipo_destino", "entidade"),
                relacao=t['relacao'],
                fonte=t.get("fonte", "?"),
                evidencia=t.get("evidencia", ""),
            )
        total = sessao.run("MATCH (n) RETURN count(n) AS n").single()["n"]
        rels = sessao.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
    print(f"Memgraph carregado: {total} nós, {rels} relações")

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
    triplas = mod04.carregar_triplas()  # Carrega as triplas do Hollow Knight
    try:
        driver = GraphDatabase.driver(URI, auth=("", ""))
        driver.verify_connectivity()
    except Exception as erro:
        raise SystemExit(
            f"Não foi possível conectar ao Memgraph em {URI} ({erro}).\n"
            "Suba o container: docker run -it -p 7687:7687 -p 7444:7444 memgraph/memgraph-mage"
        )

    carregar_no_memgraph(driver, triplas)

    # Consultas sobre a lore do Hollow Knight
    consultas_lore = {
        "Relações familiares do Cavaleiro": """
            MATCH (cavaleiro:ENTIDADE {nome: 'Cavaleiro'})-[:RELACAO]->(parente)
            WHERE parente.tipo IN ['personagem', 'PESSOA']
            RETURN DISTINCT cavaleiro.nome AS entidade, parente.nome AS relacionado
            LIMIT 10
        """,
        
        "Personagens vs chefes (lutas)": """
            MATCH (p:ENTIDADE)-[r:RELACAO]->(c:ENTIDADE)
            WHERE r.tipo IN ['luta_contra', 'batalha_contra', 'combate_contra']
            RETURN p.nome AS personagem, c.nome AS chefe
            LIMIT 15
        """,
        
        "Locais e seus significados": """
            MATCH (local:ENTIDADE {tipo: 'local'})
            RETURN local.nome AS local
            LIMIT 10
        """,
        
        "Itens e quem os possui": """
            MATCH (item:ENTIDADE {tipo: 'item'})-[r]->(personagem:ENTIDADE)
            RETURN DISTINCT 
                item.nome AS item, 
                personagem.nome AS dono,
                type(r) AS tipo_relacao
            LIMIT 10
        """,
    }

    print("=" * 80)
    print("🎮 EXPLORADOR DA LORE - HOLLOW KNIGHT 🎮")
    print("=" * 80)

    for titulo, cypher in consultas_lore.items():
        print(f"\n[📖] {titulo}")
        print("-" * 80)
        try:
            resultados = executar(driver, cypher)
            if resultados:
                for linha in resultados:
                    print(f"  ✓ {linha}")
            else:
                print("  (sem resultados)")
        except Exception as e:
            print(f"  ⚠️  Erro na consulta: {e}")

    # Text-to-Cypher: perguntas sobre a lore
    if "--llm" in sys.argv:
        perguntas = [
            "Quem é a mãe do Cavaleiro?",
            "Qual é a relação entre Hornet e o Cavaleiro?",
            "Que itens são necessários para derrotar a Radiância?"
        ]
        
        print("\n" + "=" * 80)
        print("🤖 CONSULTAS GERADAS POR IA (text-to-Cypher)")
        print("=" * 80)
        
        for pergunta in perguntas:
            print(f"\n[❓] {pergunta}")
            try:
                cypher = gerar_cypher_com_llm(pergunta)
                print(f"[📝] Cypher gerado: {cypher[:100]}...")
                resultados = executar(driver, cypher)
                for linha in resultados:
                    print(f"  → {linha}")
            except Exception as erro:
                print(f"  ⚠️  Consulta falhou: {erro}")

    driver.close()
    print("\n✅ Exploração da lore concluída!")

if __name__ == "__main__":
    main()

