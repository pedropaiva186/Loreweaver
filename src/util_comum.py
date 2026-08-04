import json
import os
import pathlib
import re
import time

import ollama

DIR_CORPUS = pathlib.Path(__file__).resolve().parent.parent / "data" / "hollow_knight_wiki_knowledge_pt"
DIR_DADOS = pathlib.Path(__file__).resolve().parent.parent / "data" / "hollowknight_pipeline"

CHUNK_SIZE = 2200
CHUNK_OVERLAP = 500
MODEL = "mistral:7b-instruct-v0.3-q4_K_M"


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
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + CHUNK_SIZE
        chunks.append(texto[inicio:fim].strip())
        inicio = fim - CHUNK_OVERLAP
    return [c for c in chunks if c]


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


def chamar_modelo(prompt, temperature=0.1, max_tokens=2048):
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


def escrever_json(path, conteudo):
    os.makedirs(path.parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(conteudo, f, ensure_ascii=False, indent=2)
