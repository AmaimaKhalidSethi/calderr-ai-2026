from langchain_community.vectorstores import (
    Chroma
)

from langchain_community.embeddings import (
    HuggingFaceEmbeddings
)

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)

query = "What does json.dumps do?"

results = db.similarity_search_with_score(
    query,
    k=3
)


for i, (doc, score) in enumerate(results):

    print("\n")

    print("=" * 80)

    print(
        f"Result {i+1}"
    )

    print(
        f"Score: {score}"
    )

    print(
        f"Source: "
        f"{doc.metadata.get('source')}"
    )

    print()

    print(
        doc.page_content[:1000]
    )