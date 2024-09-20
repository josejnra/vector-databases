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
    read_blog_post_page,
    split_documents,
    read_a_web_page
)
from retrieve import chat_ollama, weavite_search

if __name__ == "__main__":
    # calcule o tempo de execucão do script
    start_time = time.time()

    collection_name = "langchain_example"
    create_weaviate_collection(collection_name)

    docs_scraped = read_blog_post_page("https://lilianweng.github.io/posts/2023-06-23-agent/")
    split_docs = split_documents(docs_scraped)
    index_documents(split_docs, collection_name)

    docs_scraped = read_a_web_page("https://realpython.com/python313-free-threading-jit/")
    split_docs = split_documents(docs_scraped)
    index_documents(split_docs, collection_name)

    # docs = weavite_search("What challenges does the retrieval augmented generation approach solve?", collection_name)
    # list_collections(collection_name)
    print(chat_ollama(collection_name, "What is Task Decomposition?"))
    print(chat_ollama(collection_name, "Measure the performance improvements of python 3.13"))

    print(f"Total time: {time.time() - start_time} seconds")
