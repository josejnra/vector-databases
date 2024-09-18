import json
import warnings

warnings.filterwarnings("ignore")

import weaviate
import weaviate.classes as wvc
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.types import UUID

# # Download the data
# resp = httpx.get(
#     "https://raw.githubusercontent.com/weaviate-tutorials/quickstart/main/data/jeopardy_tiny.json"
# )
# data = json.loads(resp.text)  # Load data

SERVER_ADDRESS = "192.168.0.15"

def json_print(data: dict):
    print(json.dumps(data, indent=2))


def list_collections():
    with weaviate.connect_to_local(
        additional_config=AdditionalConfig(
            timeout=Timeout(init=30, query=60, insert=120)  # Values in seconds
        )
    ) as client:
        collections = client.collections.list_all(
            simple=False
        )  # Use `simple=False` to get comprehensive information

        print("available collections", collections)


def create_collection():
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        # resetting the collection. CAUTION: This will delete your collection
        if client.collections.exists("Question"):
            client.collections.delete("Question")

        client.collections.create(
            name="Question",
            # vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_transformers(),  # If set to "none" you must always provide vectors yourself.
            vectorizer_config=wvc.config.Configure.Vectorizer.text2vec_ollama(
                # api_endpoint="http://host.docker.internal:11434",
                api_endpoint=f"http://{SERVER_ADDRESS}:11434",
                model="all-minilm"
            ),
            generative_config=wvc.config.Configure.Generative.ollama(
                # api_endpoint="http://host.docker.internal:11434",
                api_endpoint=f"http://{SERVER_ADDRESS}:11434",
                model="llama3.1:8b"
            )
        )

        # print(questions)


def create_object() -> UUID:
    """create an object"""
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        with client.batch.dynamic() as batch:
            object_uuid = batch.add_object(
                properties={
                    "question": "Leonardo da Vinci was born in this country.",
                    "answer": "Italy",
                    "category": "Culture",
                },
                collection="Question",
            )
            print("object uuid created", object_uuid)

        with open("data.json") as f:
            data = json.loads(f.read())

        question_objs: list[dict] = []
        for d in data:
            question_objs.append({
                "answer": d["Answer"],
                "question": d["Question"],
                "category": d["Category"],
            })

        questions = client.collections.get("Question")
        questions.data.insert_many(question_objs)

    return object_uuid


def read(object_uuid: UUID):
    with weaviate.connect_to_local(
        host=SERVER_ADDRESS,
        additional_config=AdditionalConfig(
            timeout=Timeout(init=3000, query=3000, insert=120)
        )
    ) as client:
        questions = client.collections.get("Question")

        print("fetching object by id")
        json_print(questions.query.fetch_object_by_id(object_uuid).properties)

        # semantic search
        print("semantic search")
        response = questions.query.near_text(query="biology", limit=2)

        json_print(response.objects[0].properties)  # Inspect the first object

        # Generative search (single prompt)
        print("generative search (single prompt)")
        query = "Quem é José Nunes?"
        response = questions.generate.near_text(
            query=query,
            single_prompt="Answer the question: {answer}", 
            limit=1,
        )

        print("pergunta:", query)
        print("resposta", response.objects[0].generated)  # Inspect the generated text
        query = "Qual seu nome completo de José Nunes?"
        response = questions.generate.near_text(
            query=query,
            single_prompt="Answer the question: {answer}", 
            limit=1,
        )

        print("pergunta:", query)
        print("resposta", response.objects[0].generated)  # Inspect the generated text

        query = "De forma direta e curta diga em qual país José Nunes"
        response = questions.generate.near_text(
            query=query,
            single_prompt="Answer the question: {answer}", 
            limit=1,
        )
        print("pergunta:", query)
        print("resposta", response.objects[0].generated)  # Inspect the generated text

        # Generative search (grouped task)
        response = questions.generate.near_text(
            query="biology",
            grouped_task="Write a tweet with emojis about these facts.",
            limit=1,
        )

        print(response.generated)  # Inspect the generated text


def update(object_uuid: str):
    with weaviate.connect_to_local() as client:
        client.data_object.update(
            uuid=object_uuid,
            class_name="Question",
            data_object={"answer": "Florence, Italy"},
        )

        data_object = client.data_object.get_by_id(
            object_uuid,
            class_name="Question",
        )

        json_print(data_object)


def delete(object_uuid: str):
    with weaviate.connect_to_local() as client:
        json_print(client.query.aggregate("Question").with_meta_count().do())
        client.data_object.delete(uuid=object_uuid, class_name="Question")
        json_print(client.query.aggregate("Question").with_meta_count().do())


def query():
    with weaviate.connect_to_local() as client:
        response = (
            client.query.get("Question", ["question", "answer", "category"])
            .with_near_text({"concepts": "biology"})
            .with_additional("distance")
            .with_limit(2)
            .do()
        )

        json_print(response)

        # We can let the vector database know to remove results after a threshold distance!

        response = (
            client.query.get("Question", ["question", "answer"])
            .with_near_text({"concepts": ["animals"], "distance": 0.24})
            .with_limit(10)
            .with_additional(["distance"])
            .do()
        )

        json_print(response)


if __name__ == "__main__":
    create_collection()
    # list_collections()
    object_uuid = create_object()
    read(object_uuid)
