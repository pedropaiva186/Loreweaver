"""Etapa 2 — Extração de entidades e relações do domínio Hollow Knight."""

import json
from .util_comum import carregar_corpus, dividir_em_chunks, chamar_modelo, escrever_json, DIR_DADOS

PROMPT_EXTRACAO = '''Você é um extrator de conhecimento especializado em Hollow Knight.
Extraia do texto abaixo TODAS as relações factuais entre entidades identificáveis.

Responda APENAS com JSON válido no formato:
{
  "triplas": [
    {
      "origem": "...",
      "tipo_origem": "personagem|local|item|conceito|evento|organizacao|outro",
      "relacao": "...",
      "destino": "...",
      "tipo_destino": "personagem|local|item|conceito|evento|organizacao|outro",
      "evidencia": "trecho curto que justifica"
    }
  ]
}


- Use nomes de relação curtos e canônicos: A decidir.

- Extraia apenas o que está explícito no texto. Não invente.

TEXTO ({fonte}):
{text}'''


def main():
    docs = carregar_corpus()
    todas = []

    for nome, texto in docs:
        for n, chunk in enumerate(dividir_em_chunks(texto)):
            prompt = PROMPT_EXTRACAO.format(fonte=nome, text=chunk)
            resposta = chamar_modelo(prompt)
            try:
                triplas = json.loads(resposta)["triplas"]
            except Exception as erro:
                print(f"[aviso] chunk {nome}#{n}: saída inválida ({erro}); pulando")
                continue
            for t in triplas:
                t["fonte"] = f"{nome}#chunk{n}"
            todas.extend(triplas)
            print(f"{nome}#chunk{n}: {len(triplas)} triplas")

    escrever_json(DIR_DADOS / "triplas_brutas.json", {"triplas": todas})
    print(f"Total: {len(todas)} triplas brutas -> {DIR_DADOS / 'triplas_brutas.json'}")


if __name__ == '__main__':
    main()
