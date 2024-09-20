import warnings

warnings.filterwarnings("ignore")

import weaviate
from config import (
    OLLAMA_BASE_URL,
    OLLAMA_EMBEDDINGS_MODEL,
    OLLAMA_GENERATIVE_MODEL,
    SERVER_ADDRESS,
)
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_weaviate import WeaviateVectorStore


def list_collections(collection_name: str):
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        collections = client.collections.list_all()
        print("quantidade de collections:", len(collections))
        for k, _ in collections.items():
            print("collection name:", k)

        lang = client.collections.get(collection_name)
        for object in lang.generate.fetch_objects().objects:
            print(object.properties)


def weavite_search(query: str, collection_name: str, k: int = 4) -> list[Document]:
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        weaviate_db = WeaviateVectorStore(
            client=client,
            index_name=collection_name,
            text_key="text",
            embedding=OllamaEmbeddings(
                base_url=OLLAMA_BASE_URL, model=OLLAMA_EMBEDDINGS_MODEL
            ),
        )
        docs = weaviate_db.similarity_search(query, k)

        print(f"Found {len(docs)} results for query '{query}':")
        # Print the first 100 characters of each result
        for i, doc in enumerate(docs):
            print(f"\nDocument {i + 1}:")
            print(doc.metadata)
            print(doc.page_content[:100] + "...")

        return docs


def format_docs(docs: list[Document]):
    # print("docs retrieved:", len(docs))
    # for doc in docs:
    #     print(doc.model_dump(exclude={"page_content"}))
    return "\n\n".join(
        doc.page_content + " found at doc: " + doc.metadata["source"] for doc in docs
    )


def chat_ollama(collection_name: str, question: str) -> str:
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        weaviate_db = WeaviateVectorStore(
            client=client,
            index_name=collection_name,
            text_key="text",
            embedding=OllamaEmbeddings(
                base_url=OLLAMA_BASE_URL, model=OLLAMA_EMBEDDINGS_MODEL
            ),
        )
        retriever = weaviate_db.as_retriever(
            search_type="similarity", search_kwargs={"k": 6}
        )

        llm = ChatOllama(
            base_url=OLLAMA_BASE_URL, model=OLLAMA_GENERATIVE_MODEL, temperature=0
        )

        template = """Use the following pieces of context to answer the question at the end.
        If you don't know the answer, just say that you don't know, don't try to make up an answer.
        Use three sentences maximum and keep the answer as concise as possible.
        List the documents found as reference for this answer and don't repeat the same document.
        Always say "thanks for asking!" at the end of the answer.

        {context}

        Question: {question}

        Helpful Answer:"""

        custom_rag_prompt = PromptTemplate.from_template(template)

        rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | custom_rag_prompt
            | llm
            | StrOutputParser()
        )

        return rag_chain.invoke(question)
