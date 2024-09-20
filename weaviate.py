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
                model="all-minilm",
                # model="paraphrase-multilingual"
            ),
            generative_config=wvc.config.Configure.Generative.ollama(
                # api_endpoint="http://host.docker.internal:11434",
                api_endpoint=f"http://{SERVER_ADDRESS}:11434",
                model="llama3.1:8b",
            ),
        )

        # print(questions)


def create_object() -> UUID:
    """create an object"""
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        questions = client.collections.get("Question")
        questions.data.insert(
            properties={
                "question": "Monalisa was created by this artist.",
                "answer": "Leonardo da Vinci",
                "category": "Culture",
            },
        )

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
        ),
    ) as client:
        questions = client.collections.get("Question")

        print("fetching object by id")
        json_print(questions.query.fetch_object_by_id(object_uuid).properties)

        # semantic search
        print("semantic search\n")
        query = "biology"
        response = questions.query.near_text(query=query, limit=2)
        print("query:", query)
        json_print(response.objects[0].properties)  # Inspect the first object

        query = "seu madroga?"
        response = questions.query.near_text(query=query, limit=2)
        print("query:", query)
        for obj in response.objects:
            json_print(obj.properties)

        for object in questions.generate.fetch_objects().objects:
            json_print(object.properties)


def generative_search():
    with weaviate.connect_to_local(
        host=SERVER_ADDRESS,
        additional_config=AdditionalConfig(
            timeout=Timeout(init=3000, query=3000, insert=120)
        ),
    ) as client:
        questions = client.collections.get("Question")

        # Generative search (single prompt)
        print("generative search (single prompt)")
        query = "Quem é Seu Madroga?"
        response = questions.generate.near_text(
            query=query,
            single_prompt="Answer the question: {answer}",
            limit=1,
        )

        print("pergunta:", query)
        print("resposta", response.objects[0].generated)  # Inspect the generated text
        query = "Qual o nome completo de Seu Madroga?"
        response = questions.generate.near_text(
            query=query,
            single_prompt="Answer the question: {answer}",
            limit=1,
        )

        print("pergunta:", query)
        print("resposta", response.objects[0].generated)  # Inspect the generated text

        query = "De forma direta e curta diga em qual país Seu Madroga vive"
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
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        questions = client.collections.get("Question")
        questions.data.update(
            uuid=object_uuid,
            properties={"answer": "Florence, Italy"},
        )

        data_object = questions.query.fetch_object_by_id(object_uuid)

        json_print(data_object.properties)


def delete(object_uuid: str):
    with weaviate.connect_to_local(host=SERVER_ADDRESS) as client:
        questions = client.collections.get("Question")
        for obj in questions.iterator():
            json_print(obj.uuid, obj.properties)
        questions.data.delete_by_id(uuid=object_uuid)
        for obj in questions.iterator():
            json_print(obj.uuid, obj.properties)


if __name__ == "__main__":
    create_collection()
    # list_collections()
    object_uuid = create_object()
    read(object_uuid)
    # update(object_uuid)
    # delete(object_uuid)
