import bs4
import weaviate
import weaviate.classes as wvc
from config import OLLAMA_BASE_URL, OLLAMA_EMBEDDINGS_MODEL, SERVER_ADDRESS
from langchain_community.document_loaders import WebBaseLoader
from langchain_core.documents import Document
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_weaviate import WeaviateVectorStore


def read_web_page(url: str) -> list[Document]:
    """Read the content of a web page."""
    # Only keep post title, headers, and content from the full HTML.
    bs4_strainer = bs4.SoupStrainer(
        class_=("post-title", "post-header", "post-content")
    )
    loader = WebBaseLoader(
        web_paths=(url,),
        bs_kwargs={"parse_only": bs4_strainer},
    )
    docs = loader.load()

    print(len(docs[0].page_content))
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    """Split documents into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    all_splits = text_splitter.split_documents(docs)

    print(len(all_splits))
    # print(all_splits[0])
    return all_splits


def create_weaviate_collection(collection_name: str):
    """Create a Weaviate collection."""
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        if client.collections.exists(collection_name):
            client.collections.delete(collection_name)

        client.collections.create(
            name=collection_name,
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_ollama(
                api_endpoint=OLLAMA_BASE_URL,
                model="all-minilm",
            ),
            generative_config=wvc.config.Configure.Generative.ollama(
                api_endpoint=OLLAMA_BASE_URL,
                model=OLLAMA_EMBEDDINGS_MODEL,
            ),
        )


def index_documents(docs: list[Document], collection_name: str) -> WeaviateVectorStore:
    """Index documents using Ollama."""
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        return WeaviateVectorStore(
            client=client,
            index_name=collection_name,
            text_key="text",
        ).from_documents(
            documents=docs,
            embedding=OllamaEmbeddings(
                base_url=OLLAMA_BASE_URL, model=OLLAMA_EMBEDDINGS_MODEL
            ),
            client=client,
            index_name=collection_name,
        )
