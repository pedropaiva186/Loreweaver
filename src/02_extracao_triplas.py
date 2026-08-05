"""Etapa 2 — Extração de entidades e relações do domínio Hollow Knight."""

import json
from util_comum import carregar_corpus, dividir_em_chunks, chamar_modelo, escrever_json, DIR_DADOS, extrair_json_do_texto

PROMPT_EXTRACAO = '''Voce e um extrator de conhecimento especializado em Hollow Knight.
Extraia do texto abaixo TODAS as relacoes factuais entre entidades identificaveis.
Responda APENAS com um JSON valido no seguinte formato:
{
  "triplas": [
    {
      "origem": "...",
      "tipo_origem": "tipos canonicos de entidade",
      "relacao": "...",
      "destino": "...",
      "tipo_destino": "tipos canonicos de entidade",
      "evidencia": "trecho curto que justifica"
    }
  ]
}
Regras:
- Ignore acentos e cedilha.
- Extraia apenas informacoes que estejam explicitamente presentes no texto.
- Nao invente entidades nem relacoes.
- Sempre utilize exatamente um dos seguintes tipos canonicos de entidade:
  - item
  - local
  - npc
  - conceito
  - inimigo
  - habilidade
  - chefe
  - vendedor
  - grupo
- Caso uma entidade possa pertencer a mais de um tipo, escolha o mais especifico.
  Exemplos:
  - Mercador -> vendedor
  - Hornet -> chefe (quando o texto se referir ao chefe) ou npc (quando se referir a personagem da historia)
  - Mantis Traitor -> chefe
  - Vengefly -> inimigo
- Sempre utilize exatamente um dos seguintes tipos canonicos de relacao:
  - contem
  - derrota
  - usa
  - localizado_em
  - afeta
  - requer
  - executa_habilidade
  - leva_a
  - vende
  - dropa
  - libera
  - cria
  - eh_inimigo_de
  - eh_relatado_por
  - eh_membro_de
  - protege
- Caso uma relacao possa ser expressa por mais de um tipo, escolha o mais especifico.
  Exemplos:
  - Gruz Mae localizado_em Ruinas Esquecidas (nao usa "contem")
  - Salubra vende Encanto de Foco (nao usa "dropa")
  - Derrota de Gruz Mae libera passagem -> usa "libera", nao "derrota"
  - Xero protege Tumulo dos Guerreiros (nao usa "localizado_em")
- O campo "evidencia" deve conter um trecho curto do texto que comprove a tripla.
TEXTO ({fonte}):
{text}
'''


def main():
    docs = carregar_corpus()
    todas = []

    for nome, texto in docs:
        for n, chunk in enumerate(dividir_em_chunks(texto)):
            prompt = PROMPT_EXTRACAO.format(fonte=nome, text=chunk)
            resposta = chamar_modelo(prompt)
            try:
                triplas = extrair_json_do_texto(resposta)["triplas"]
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
