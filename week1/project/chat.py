from dotenv import load_dotenv

from langchain_groq import ChatGroq

from langchain_community.vectorstores import (
    Chroma
)

from langchain_community.embeddings import (
    HuggingFaceEmbeddings
)

load_dotenv()

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

db = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)


def retrieve_context(query):

    results = db.similarity_search(
        query,
        k=3
    )

    return "\n\n".join(
        doc.page_content
        for doc in results
    )


def build_prompt(
    context,
    question
):

    return f"""
You are a Python documentation assistant.

Answer only using the provided context.

If the answer cannot be found,
say so.

Context:

{context}

Question:

{question}
"""


while True:

    question = input(
        "\nAsk: "
    )

    if question.lower() in [
        "quit",
        "exit"
    ]:
        break

    context = retrieve_context(
        question
    )

    prompt = build_prompt(
        context,
        question
    )

    response = llm.invoke(
        prompt
    )

    print(
        "\nAnswer:\n"
    )

    print(
        response.content
    )