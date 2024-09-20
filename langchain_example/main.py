"""
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_API_KEY="..."
"""

import time
import warnings

warnings.filterwarnings("ignore")

from indexing import (
    create_weaviate_collection,
    index_documents,
    read_web_page,
    split_documents,
)
from retrieve import chat_ollama, weavite_search

if __name__ == "__main__":
    # calcule o tempo de execucão do script
    start_time = time.time()

    docs_scraped = read_web_page("https://lilianweng.github.io/posts/2023-06-23-agent/")
    split_docs = split_documents(docs_scraped)

    collection_name = "langchain_example"
    create_weaviate_collection(collection_name)
    index_documents(split_docs, collection_name)
    # docs = weavite_search(collection_name)
    # list_collections(collection_name)
    print(chat_ollama(collection_name, "What is Task Decomposition?"))

    print(f"Total time: {time.time() - start_time} seconds")
