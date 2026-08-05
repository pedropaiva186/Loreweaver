import json
import os
import pathlib
import re
import time

import tiktoken
import httpx
import ollama

DIR_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "data" / "hollow_knight_wiki_knowledge_pt"
DIR_DADOS = pathlib.Path(__file__).resolve().parent.parent / "data" / "hollowknight_pipeline"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 80
MODEL = "qwen2.5:7b-instruct-q4_K_M" #mistral:7b-instruct-v0.3-q4_K_M



def carregar_corpus():
    docs = []
    if not DIR_CORPUS.exists():
        raise SystemExit(f"Corpus não encontrado em {DIR_CORPUS}")
    for caminho in sorted(DIR_CORPUS.glob("*.md")):
        docs.append((caminho.name, caminho.read_text(encoding="utf-8")))
    if not docs:
        raise SystemExit(f"Nenhum documento encontrado em {DIR_CORPUS}")
    return docs


def dividir_em_chunks(texto):
    # Utiliza o tokenizador do tiktoken (muito rápido em C)
    encoder = tiktoken.get_encoding("cl100k_base")
    tokens = encoder.encode(texto)
    total_tokens = len(tokens)

    if total_tokens <= (CHUNK_SIZE * 1.2):
        return [texto]
    
    chunks = []
    inicio = 0

    while inicio < len(tokens):
        # Pega a janela de tokens
        chunk_tokens = tokens[inicio : inicio + CHUNK_SIZE]
        # Decodifica de volta para texto legível
        chunk_texto = encoder.decode(chunk_tokens)
        chunks.append(chunk_texto)
        
        # Avança considerando a sobreposição (overlap)
        inicio += CHUNK_SIZE - CHUNK_OVERLAP
        
    return chunks


def extrair_json_do_texto(texto):
    texto = texto.strip()
    if texto.startswith('```'):
        texto = re.sub(r"^```[a-zA-Z0-9]*\n|```$", "", texto, flags=re.MULTILINE)
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        texto = match.group(0)
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        raise ValueError(f"Não foi possível parsear JSON da resposta: {texto[:200]}...")


def chamar_modelo(prompt, temperature=0.1, max_tokens=2048, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            response = ollama.chat(
                model=MODEL,
                format="json",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": temperature,
                    "num_ctx": 8192,
                    "num_predict": max_tokens,
                }
            )
            return response["message"]["content"].strip()
        except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as erro:
            if attempt == max_retries:
                raise
            wait = 2 ** (attempt - 1)
            print(f"[aviso] erro de conexão ao chamar o modelo ({erro}); tentando novamente em {wait}s... ({attempt}/{max_retries})")
            time.sleep(wait)
        except Exception:
            raise

def chamar_modelo_sem_json(prompt, temperature=0.1, max_tokens=2048, max_retries=3):
    for attempt in range(1, max_retries + 1):
        try:
            response = ollama.chat(
                model=MODEL,
                format="",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": temperature,
                    "num_ctx": 8192,
                    "num_predict": max_tokens,
                }
            )
            return response["message"]["content"].strip()
        except (httpx.RemoteProtocolError, httpx.ConnectError, httpx.ReadTimeout) as erro:
            if attempt == max_retries:
                raise
            wait = 2 ** (attempt - 1)
            print(f"[aviso] erro de conexão ao chamar o modelo ({erro}); tentando novamente em {wait}s... ({attempt}/{max_retries})")
            time.sleep(wait)
        except Exception:
            raise


def escrever_json(path, conteudo):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)

def extrair_json_seguro(resposta, max_tentativas=3):
    """Extrai JSON com recuperação de falhas"""
    # Tenta remover markdown backticks
    resposta = resposta.replace("```json", "").replace("```", "")
    
    # Tenta encontrar o JSON válido mais longo
    import re
    json_matches = re.findall(r'\{.*\}', resposta, re.DOTALL)
    
    for tentativa, match in enumerate(json_matches):
        try:
            return json.loads(match)
        except json.JSONDecodeError as e:
            if tentativa == len(json_matches) - 1:
                raise e
            continue