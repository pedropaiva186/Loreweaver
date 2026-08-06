"""Etapa 7 — O mesmo grafo em um banco de grafos: Memgraph + Cypher.

Carrega as triplas refinadas no Memgraph usando Rótulos e Relações Nativas,
executa consultas Cypher e demonstra text-to-Cypher com schema rigoroso.
"""

import json
import sys
import re
from importlib import import_module

from neo4j import GraphDatabase

from util_comum import DIR_DADOS, MODEL, chamar_modelo_sem_json

URI = "bolt://localhost:7687"

# Listas de validação/normalização conforme o schema
ENTIDADES_VALIDAS = {
    "item", "localizacao", "npc", "conceito", "inimigo", 
    "habilidade", "chefe", "vendedor", "grupo", "protagonista"
}

RELACOES_VALIDAS = {
    "contem", "derrota", "usa", "localizado_em", "afeta", "requer",
    "executa_habilidade", "leva_a", "vende", "dropa", "libera",
    "cria", "eh_inimigo_de", "eh_relatado_por", "eh_membro_de", "protege"
}

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
        MATCH (origem:LOCALIZACAO)-[r:LEVA_A|LOCALIZADO_EM]->(destino:LOCALIZACAO)
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
  :ITEM, :LOCALIZACAO, :NPC, :CONCEITO, :INIMIGO, :HABILIDADE, :CHEFE, :VENDEDOR, :GRUPO

- PROPRIEDADES DOS NÓS:
  O único atributo de busca é 'nome'. NUNCA filtre o nome dentro do parênteses do MATCH.

- RELAÇÕES (Tipos de Aresta em MAIÚSCULAS):
  -[:CONTEM]->, -[:DERROTA]->, -[:USA]->, -[:LOCALIZADO_EM]->, -[:AFETA]->,
  -[:REQUER]->, -[:EXECUTA_HABILIDADE]->, -[:LEVA_A]->, -[:VENDE]->, -[:DROPA]->,
  -[:LIBERA]->, -[:CRIA]->, -[:EH_INIMIGO_DE]->, -[:EH_RELATADO_POR]->,
  -[:EH_MEMBRO_DE]->, -[:PROTEGE]->

EXEMPLOS DE CONSULTAS CORRETAS:
1. "O que o vendedor vende?"
   MATCH (v:VENDEDOR)-[r:VENDE]->(i:ITEM) 
   RETURN v.nome AS vendedor, i.nome AS item

2. "Qual habilidade afeta ou derrota o chefe?"
   MATCH (h:HABILIDADE)-[r:AFETA|DERROTA]->(c:CHEFE)
   RETURN h.nome AS habilidade, type(r) AS relacao, c.nome AS chefe

3. "Quais inimigos estão em Hallownest?"
   MATCH (i:INIMIGO)-[:LOCALIZADO_EM]->(l:LOCALIZACAO)
   WHERE toLower(l.nome) CONTAINS "hallownest"
   RETURN i.nome AS inimigo, l.nome AS localizacao

REGRAS CRÍTICAS:
- Use Rótulos e Tipos de Aresta diretamente na sintaxe do Cypher.
- NUNCA invente Rótulos (Labels). Use apenas os da lista acima.
- PROIBIDO usar propriedades dentro do MATCH (ex: `(:NPC {{nome: "Cavaleiro"}})` está ERRADO).
- Para filtrar nomes específicos, você deve OBRIGATORIAMENTE usar a cláusula `WHERE toLower(n.nome) CONTAINS "texto_em_minusculo"`.
- SINTAXE DO OU (|): Para múltiplas relações, NUNCA use parênteses. O correto é `-[r:AFETA|DERROTA]->` (e não `-[r:(AFETA|DERROTA)]->`).
- FUNÇÃO TYPE: Para retornar o tipo de uma relação, SEMPRE use a função `type(r)`. NUNCA use `r.type`.
- Obrigatoriamente atribua um alias com 'AS' para CADA campo no RETURN (exemplo: v.nome AS vendedor).
- Responda APENAS com o código Cypher puro, sem blocos de markdown.
- Os atributos todos estao em minusculo

PERGUNTA: {pergunta}
"""

# Normalizando identificadores
def sanitizar_identificador(texto: str, padrao: str = "OUTRO") -> str:
    if not texto:
        return padrao
    limpo = re.sub(r'[^a-zA-Z0-9_]', '_', texto).lower().strip('_')
    return limpo.upper() if limpo else padrao

# Responder a pergunta do usuário usando os resultados do grafo como contexto
def responder_pergunta_com_graphrag(pergunta, resultados_grafo):
    prompt_rag = f"""
    Você é um assistente especialista na lore de Hollow Knight.
    Responda à pergunta do usuário utilizando APENAS os fatos extraídos do banco de dados de grafos abaixo.

    PERGUNTA DO USUÁRIO:
    {pergunta}

    DADOS RECUPERADOS DO GRAFO:
    {json.dumps(resultados_grafo, ensure_ascii=False)}

    RESPOSTA (seja claro, conciso e natural):
    """

    return chamar_modelo_sem_json(prompt_rag, temperature=0.2)

# Função para carregar triplas refinadas no Memgraph usando Rótulos e Relações Nativas
def carregar_no_memgraph(driver, triplas):
    with driver.session() as sessao:
        sessao.run("MATCH (n) DETACH DELETE n")
        for t in triplas:
            # 1. etapa de normalização de tipos de origem, destino e relação
            raw_origem = t.get("tipo_origem", "conceito").lower()
            raw_destino = t.get("tipo_destino", "conceito").lower()
            raw_rel = t.get("relacao", "afeta").lower()

            # Valida com o schema (fallback para CONCEITO / AFETA se inválido)
            label_origem = sanitizar_identificador(raw_origem if raw_origem in ENTIDADES_VALIDAS else "conceito")
            label_destino = sanitizar_identificador(raw_destino if raw_destino in ENTIDADES_VALIDAS else "conceito")
            tipo_relacao = sanitizar_identificador(raw_rel if raw_rel in RELACOES_VALIDAS else "afeta")

            # 2. Insere o nó e aresta no banco de grafos utilizando Rótulos e Relações Nativas
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
    cypher = chamar_modelo_sem_json(
        PROMPT_TEXT2CYPHER.format(pergunta=pergunta),
        temperature=0.0,
        max_tokens=1024,
    ).strip()
    cypher = re.sub(r"^```(?:cypher)?\n|```$", "", cypher, flags=re.IGNORECASE).strip()
    return cypher


def carregar_triplas():
    caminho = DIR_DADOS / "triplas_refinadas.json"
    if not caminho.exists():
        raise SystemExit(f"Arquivo não encontrado: {caminho}")
    return json.loads(caminho.read_text(encoding='utf-8'))["triplas"]


def main():
    triplas = carregar_triplas()
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
    print("EXPLORADOR DA LORE — HOLLOW KNIGHT (CYPHER NATIVO)")
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
            "Como eu faco um script python que gera consultas cypher para o Memgraph?",
        ]
        
        print("\n" + "=" * 80)
        print("CONSULTAS GERADAS POR IA (text-to-Cypher)")
        print("=" * 80)
        
        for pergunta in perguntas:
            print(f"\n{pergunta}")
            try:
                cypher = gerar_cypher_com_llm(pergunta)
                print(f"Cypher gerado: {cypher}")
                resultados = executar(driver, cypher)
                #for linha in resultados:
                #    print(f"  → {linha}")
                resposta_final = responder_pergunta_com_graphrag(pergunta, resultados)
                print(f"Resposta gerado pelo GraphRAG: {resposta_final}")
            except Exception as erro:
                print(f"Consulta falhou: {erro}")

    driver.close()
    print("\nExploração da lore concluída!")

if __name__ == "__main__":
    main()