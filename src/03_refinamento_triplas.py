"""Etapa 3 — Refinamento e normalização do grafo de Hollow Knight (Com Batching Seguro)."""

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
    # sinonimos para derrota
    "vence": "derrota",
    "venceu": "derrota",
    "derrotou": "derrota",
    "mata": "derrota",
    "matou": "derrota",
    "elimina": "derrota",
    "eliminou": "derrota",
    "destruiu": "derrota",
    "destrói": "derrota",

    # sinonimos para uso
    "utiliza": "usa",
    "usufrui": "usa",
    "emprega": "usa",
    "maneja": "usa",
    "porta": "usa",
    "equipa": "usa",

    # sinônimos para localização
    "esta_em": "localizado_em",
    "fica_em": "localizado_em",
    "vive_em": "localizado_em",
    "habita": "localizado_em",
    "reside_em": "localizado_em",
    "encontra_se_em": "localizado_em",
    "situado_em": "localizado_em",

    # sinônimos para pertencimento
    "pertence_a": "membro_de",
    "faz_parte_de": "membro_de",
    "integra": "membro_de",

    # sinonimos para criação criação
    "criou": "cria",
    "construiu": "cria",
    "forjou": "cria",

    # sinonimos para origem
    "nasceu_em": "origina_se_em",
    "originou_se_em": "origina_se_em",

    # sinonimos para controle
    "governa": "lidera",
    "lider": "lidera",
    "comanda": "lidera",

    # sinonimos para proteção
    "protege": "defende",
    "guarda": "defende",

    # sinonimos de infecção
    "infecta": "infectou",
    "corrompe": "infectou",
    "corrompeu": "infectou",

    # sinonimos de relações familiares
    "filho_de": "eh_filho_de",
    "pai_de": "e_pai_de",
    "mae_de": "e_mae_de",

    # sinônimos para relações genéricas
    "e_um": "eh_um",
    "é_um": "eh_um",
}

INVERSAS = {
     # Família
    "e_pai_de": "eh_filho_de",
    "e_mae_de": "eh_filho_de",
    "contem": "localizado_em",
    "possui_local": "localizado_em",
    "tem_membro": "membro_de",
    "liderado_por": "lidera",
    "criado_por": "cria",
    "forjado_por": "forja",
    "derrotado_por": "derrota",
    "protegido_por": "defende",
    "infectado_por": "infectou",
    "origem_de": "origina_se_em",
    "pertence_a": "possui",
    "aparece_em": "possui_personagem"
}

PROMPT_RESOLUCAO = '''A lista abaixo contém nomes de entidades do universo Hollow Knight.
Identifique nomes que se referem à MESMA entidade dentro desta lista.
Retorne um JSON com os agrupamentos no formato:
{{"grupos": [{{"canonico": "Nome Canônico", "aliases": ["variação 1", "variação 2"]}}]}}

Apenas inclua grupos quando houver mais de uma variação para a mesma entidade no lote.

NOMES:
{nomes}'''


def eh_entidade_valida(nome: str) -> bool:
    #Utilizado para evitar o envio de frases muito grandes como entidades
    if not nome or str(nome).lower() in ("none", "null", "?"):
        return False
    s = str(nome).strip()
    return len(s) <= 50 and len(s.split()) <= 6


def normalizar_nome(nome):
    # Converte tudo para minúsculo logo no início
    n = " ".join(str(nome).lower().split())
    # Remove os artigos no início (o, a, os, as)
    n = re.sub(r"^o |^a |^os |^as ", "", n)
    # Remove os acentos
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

    # 1. Primeira passagem: validação, normalização algorítmica e remoção de ruídos
    validas = []
    for i, t in enumerate(triplas):
        if not validar_tripla(t) or t["evidencia"] in ("", None):
            continue
        
        origem = normalizar_nome(t["origem"])
        destino = normalizar_nome(t["destino"])
        
        # Filtra frases muito longas ou valores inválidos
        if not eh_entidade_valida(origem) or not eh_entidade_valida(destino):
            continue
            
        t["origem"] = origem
        t["destino"] = destino
        normalizar_relacao(t)
        validas.append(t)
        
    triplas = validas

    # -------------------------------------------------------------------------
    # PONTO DE CHECAGEM: Resolução de Entidades por Batching via LLM
    # -------------------------------------------------------------------------
    arquivo_checkpoint = DIR_DADOS / "resolucao_entidades_checkpoint.json"
    
    mapa_aliases = {}
    if arquivo_checkpoint.exists():
        print(f"  [checkpoint] Carregando progresso anterior de: {arquivo_checkpoint}")
        mapa_aliases = json.loads(arquivo_checkpoint.read_text(encoding="utf-8"))
    
    todos_nomes = sorted({t["origem"] for t in triplas} | {t["destino"] for t in triplas})
    
    nomes_processados = set(mapa_aliases.keys())
    nomes_para_processar = [n for n in todos_nomes if n not in nomes_processados]
    
    batch_size = 30
    
    if nomes_para_processar:
        print(f"  [LLM] Processando {len(nomes_para_processar)} entidades em lotes de {batch_size}...")
        
        for i in range(0, len(nomes_para_processar), batch_size):
            batch = nomes_para_processar[i : i + batch_size]
            prompt = PROMPT_RESOLUCAO.format(nomes="\n".join(f"- {n}" for n in batch))
            
            try:
                resposta = chamar_modelo(prompt, temperature=0.0)
                resposta_limpa = re.sub(r"^```(?:json)?\n|```$", "", resposta.strip(), flags=re.IGNORECASE).strip()
                
                dados = json.loads(resposta_limpa)
                grupos = dados.get("grupos", [])
                
                for grupo in grupos:
                    canonico = grupo.get("canonico")
                    if not canonico:
                        continue
                        
                    # Registra o canônico no mapa apontando para ele mesmo
                    mapa_aliases[canonico] = canonico
                    
                    for alias in grupo.get("aliases", []):
                        mapa_aliases[alias] = canonico
                
                # Garante que todos do lote tenham entrada no mapa (identidade por padrão)
                for n in batch:
                    if n not in mapa_aliases:
                        mapa_aliases[n] = n
                        
                escrever_json(arquivo_checkpoint, mapa_aliases)
                print(f"  [batch {i // batch_size + 1}] Checkpoint atualizado ({len(mapa_aliases)} entradas no mapa).")
                
            except Exception as err:
                print(f"  [erro] Falha no lote {i // batch_size + 1}: {err}. Salvando estado atual...")
                escrever_json(arquivo_checkpoint, mapa_aliases)
                break
    else:
        print("  [checkpoint] Todas as entidades já foram processadas.")

    # 2. Aplicação do nome canônico para origem e destino das triplas
    for t in triplas:
        t["origem"] = mapa_aliases.get(t["origem"], t["origem"])
        t["destino"] = mapa_aliases.get(t["destino"], t["destino"])

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