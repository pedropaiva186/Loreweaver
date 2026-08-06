"""Etapa 2 — Extração de entidades e relações do domínio Hollow Knight."""

import json
from util_comum import carregar_corpus, dividir_em_chunks, chamar_modelo, escrever_json, DIR_DADOS, extrair_json_do_texto

PROMPT_EXTRACAO = '''Voce e um extrator de conhecimento especializado em Hollow Knight.
Extraia do texto abaixo TODAS as relacoes factuais entre entidades identificaveis.
Responda APENAS com um JSON valido no seguinte formato:
{{
  "triplas": [
    {{
      "origem": "...",
      "tipo_origem": "tipos canonicos de entidade",
      "relacao": "...",
      "destino": "...",
      "tipo_destino": "tipos canonicos de entidade",
      "evidencia": "trecho curto que justifica"
    }}
  ]
}}
Regras:
- Ignore acentos e cedilha.
- Extraia apenas informacoes que estejam explicitamente presentes no texto.
- Nao invente tipos de entidade nem tipos de relacao.
  - Utilize apenas os tipos canonicos listados neste prompt.
  - Se um fato nao puder ser representado corretamente utilizando um dos tipos de relacao canonicos, nao extraia essa tripla.
  - Nao tente representar um fato utilizando uma relacao incorreta apenas para encaixa-lo na lista.
- Sempre utilize exatamente um dos seguintes tipos canonicos de entidade:
  - protagonista (Apenas o cavaleiro/knight é o protagonista)
  - item
  - localizacao
  - npc
  - inimigo
  - habilidade
  - chefe
  - vendedor (Vende algum item ou habilidade)
  - grupo
  - conceito (Tudo que não se encaixa nos outros tipos.)
- Caso uma entidade possa pertencer a mais de um tipo, escolha o mais especifico.
  Exemplos:
  - Mercador -> vendedor
  - Hornet -> chefe (quando o texto se referir ao chefe) ou npc (quando se referir a personagem da historia)
  - Mantis Traitor -> chefe
  - Vengefly -> inimigo
- Sempre utilize exatamente um dos seguintes tipos canonicos de relacao:
  - contem
  - derrota (uma origem derrota um destino)
  - usa (uma origem usa um destino do tipo item)
  - localizado_em
  - afeta
  - requer
  - executa_habilidade (uma origem executa um destino do tipo habilidade)
  - leva_a (uma origem do tipo local leva a um destino do tipo local)
  - vende (uma origem do tipo vendedor vende um destino do tipo item ou habilidade)
  - dropa (uma origem do tipo inimigo ou chefe dropa um destino do tipo item ou habilidade)
  - libera (uma origem do tipo inimigo ou chefe libera um destino do tipo localizacao)
  - cria 
  - eh_inimigo_de 
  - eh_relatado_por
  - eh_membro_de
  - protege
- Caso uma relacao possa ser expressa por mais de um tipo relacionado, escolha o mais especifico.
  Exemplos:
  - Gruz Mae localizado_em Ruinas Esquecidas (nao usa "contem")
  - Salubra vende Encanto de Foco (nao usa "dropa")
  - Derrota de Gruz Mae libera passagem -> use "libera", nao "derrota"
- A única exceção à regra de exclusividade acima é a relação "localizado_em". 
  - Se o tipo de relação mais específico escolhido (ex: "protege") implicar fisicamente na presença da entidade no local, você DEVE extrair a relação específica E TAMBÉM gerar uma segunda tripla usando "localizado_em".
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
