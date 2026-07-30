import os
import re
import mwclient
import mwparserfromhell

# 1. Configuração do ambiente e conexão
SITE_DOMAIN = 'hollowknight.fandom.com'
PATH = '/pt/'  # Altere para '/' se desejar a wiki em inglês
OUTPUT_DIR = 'hollow_knight_knowledge_base'

os.makedirs(OUTPUT_DIR, exist_ok=True)

site = mwclient.Site(SITE_DOMAIN, path=PATH)
site.connection.headers['User-Agent'] = "HollowKnightKnowledgeBase/1.0 (victormrdv2@@exemplo.com)"

def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos para nomes de arquivos no Windows."""
    return re.sub(r'[\\/*?:"<>|]', '_', filename)

def clean_wikitext_to_markdown(raw_wikitext: str) -> str:
    """
    Processa o wikitext bruto e remove navboxes, botões de atalho,
    tabelas mecânicas, links de idiomas e resíduos de imagens.
    """
    code = mwparserfromhell.parse(raw_wikitext)

    # 1. REMOVER TEMPLATES/PREDEFINIÇÕES
    for template in code.filter_templates():
        try:
            code.remove(template)
        except ValueError:
            pass

    # 2. REMOVER TAGS HTML / PARSER
    tags_to_remove = ['gallery', 'tabber', 'script', 'style', 'ref', 'noinclude']
    for tag in code.filter_tags():
        if tag.tag.lower() in tags_to_remove:
            try:
                code.remove(tag)
            except ValueError:
                pass

    text = str(code)

    # 3. REMOVER TABELAS DA WIKI ({| ... |})
    # Remove blocos inteiros de tabelas (que contêm dados de %, dano, etc.)
    text = re.sub(r'\{\|.*?\|\}', '', text, flags=re.DOTALL)

    # 4. REMOVER LINHAS DE NAVEGAÇÃO COM "BOLINHAS" (•)
    # Se uma linha contém 2 ou mais "•", é garantido que seja um menu de navegação horizontal
    text = re.sub(r'^.*?(?:•.*?){2,}.*$\n?', '', text, flags=re.MULTILINE)

    # 5. REMOVER LINKS DE IDIOMAS ATUALIZADO (Interwikis)
    # Pega links complexos como de:Vollständigkeit_(Hollow_Knight)
    text = re.sub(r'^[a-z]{2,3}:.*$\n?', '', text, flags=re.MULTILINE | re.IGNORECASE)

    # 6. REMOVER IMAGENS E ARTEFATOS ANTES DE LIMPAR OS LINKS
    # Remove links inteiros que contenham palavras-chave de imagem
    text = re.sub(r'\[\[[^\]]*(?:Ficheiro|File|Imagem|Image|thumb|px)[^\]]*\]\]', '', text, flags=re.IGNORECASE)
    # Remove qualquer linha solta que tenha sobrado com "thumb|263x263px" (visto na imagem)
    text = re.sub(r'^.*?(?:thumb|\d+px).*$\n?', '', text, flags=re.MULTILINE | re.IGNORECASE)

    # 7. REMOVER TEXTOS FIXOS E COMENTÁRIOS
    text = re.sub(r'(?i)Tabela de Conteúdos', '', text)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

    # 8. CONVERTER LINKS INTERNOS WIKI
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)

    # 9. FORMATAÇÃO WIKITEXT -> MARKDOWN
    text = re.sub(r'=====(.*?)=====', r'##### \1', text)
    text = re.sub(r'====(.*?)====', r'#### \1', text)
    text = re.sub(r'===(.*?)===', r'### \1', text)
    text = re.sub(r'==(.*?)==', r'## \1', text)
    text = re.sub(r"''''*(.*?)''''*", r'**\1**', text)
    text = re.sub(r"''*(.*?)''*", r'*\1*', text)

    # 10. HIGIENIZAÇÃO FINAL
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)

    return text.strip()


def export_wiki_articles():
    print("Iniciando extração dos artigos...")
    
    # Busca apenas artigos principais (namespace 0 ignora páginas de discussão, predefinições, etc.)
    for page in site.allpages(namespace=0):
        title = page.name
        
        # 1. Ignorar Redirecionamentos (Redirecionam para a página principal do assunto)
        if page.redirect:
            print(f"⏩ Pulando redirecionamento: {title}")
            continue

        wikitext = page.text()

        # 2. Ignorar páginas sem conteúdo legível
        if not wikitext or not wikitext.strip():
            continue

        print(f"📄 Processando: {title}")

        # 3. Executar o pipeline de limpeza
        markdown_content = clean_wikitext_to_markdown(wikitext)

        # Se após a limpeza o artigo ficou vazio (era composto só de infobox/botões), pula
        if not markdown_content.strip():
            continue

        # 4. Salvar o arquivo Markdown
        file_title = sanitize_filename(title)
        file_path = os.path.join(OUTPUT_DIR, f"{file_title}.md")

        with open(file_path, 'w', encoding='utf-8') as f:
            # Escreve o título do artigo no topo como H1
            f.write(f"# {title}\n\n")
            f.write(markdown_content)

    print(f"\n✅ Concluído! Todos os artigos limpos foram salvos em: {OUTPUT_DIR}")

if __name__ == '__main__':
    export_wiki_articles()