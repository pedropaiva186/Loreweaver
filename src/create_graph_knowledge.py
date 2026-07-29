import os
import math

# important parameters to do chunking in big files (all values are counting the characters)
CHUNK_THRESHOLD = 4000
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 250

'''
#
# Functions Section
#
'''

def create_knowledge_graph(folder_path : str):
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_name = os.path.join(root, file)
            process_file(file_name)

def chunk_content(content : str) -> list:
    content_chunked = list()

    for i in range(math.ceil(len(content) / CHUNK_SIZE)):
        content_chunked.append(content[max((i * CHUNK_SIZE) - CHUNK_OVERLAP, 0): min(((i + 1) * CHUNK_SIZE) + CHUNK_OVERLAP, len(content))])

    return content_chunked

def extrating_ontologies(chunks : list):
    print(chunks)

def process_file(file_path : str):
    content = ''
    content_chunked = list()

    with open(file_path, 'r') as f:
        content = f.read()

    if len(content) > CHUNK_THRESHOLD: # process big files with chunking
        content_chunked = chunk_content(content)
    else:
        content_chunked.append(content)

    extrating_ontologies(content_chunked)

'''
#
# Code Section
#
'''

wiki_path = 'data/hollow_knight_wiki_pt'

create_knowledge_graph(wiki_path)