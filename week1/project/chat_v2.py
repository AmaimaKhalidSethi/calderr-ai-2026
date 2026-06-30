from dotenv import load_dotenv

from langchain_groq import ChatGroq

from langchain_community.vectorstores import Chroma

from langchain_community.embeddings import (
    HuggingFaceEmbeddings
)

from langchain_core.prompts import PromptTemplate

# ====================================
# Load Environment Variables
# ====================================

load_dotenv()


# ====================================
# Load Embedding Model
# ====================================

print("Loading Embedding Model...")

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)


# ====================================
# Load Existing Chroma Database
# ====================================

print("Loading Chroma Database...")

db = Chroma(
    persist_directory="chroma_db",
    embedding_function=embeddings
)


# ====================================
# Load Groq LLM
# ====================================

print("Loading Groq Model...")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)


# ====================================
# Prompt Template
# ====================================

prompt = PromptTemplate.from_template(
"""
You are an expert Python documentation assistant.

Use ONLY the provided context.

When answering:

1. First provide a concise definition.
2. Then explain it in simple terms.
3. Mention important usage details if available.
4. If the answer is not in context, say so.

Context:

{context}

Question:

{question}
"""
)


# ====================================
# Retrieval
# ====================================

def retrieve_with_scores(query):

    results = db.similarity_search_with_score(
        query,
        k=5
    )

    return results


# ====================================
# Display Retrieval Results
# ====================================

def show_retrieval(results):

    print("\n")
    print("=" * 80)
    print("RETRIEVED DOCUMENTS")
    print("=" * 80)

    for i, (doc, score) in enumerate(results):

        print(f"\nRank #{i+1}")

        print(
            f"Score: {score:.4f}"
        )

        print(
            f"Source: "
            f"{doc.metadata.get('source')}"
        )

        print("\nChunk Preview:\n")

        print(
            doc.page_content[:500]
        )

        print("\n" + "-" * 80)


# ====================================
# Build Context
# ====================================

def build_context(results):

    return "\n\n".join(
        doc.page_content
        for doc, score in results
    )


def get_sources(results):

    sources = []

    for doc, score in results:

        source = doc.metadata.get(
            "source",
            "Unknown"
        )

        if source not in sources:
            sources.append(source)

    return sources

# ====================================
# Main Chat Loop
# ====================================

print("\n")
print("=" * 80)
print("PYTHON DOCS RAG ASSISTANT")
print("=" * 80)

while True:

    question = input("\nAsk: ")

    if question.lower() in [
        "exit",
        "quit"
    ]:
        print("\nGoodbye!")
        break

    try:

        results = retrieve_with_scores(
            question
        )

        show_retrieval(
            results
        )

        context = build_context(
            results
        )

        print(
            f"\nContext Length: "
            f"{len(context)} characters"
        )

        prompt_text = prompt.format(
            context=context,
            question=question
        )

        response = llm.invoke(
            prompt_text
        )

        print("\n")
        print("=" * 80)
        print("ANSWER")
        print("=" * 80)

        print(
            response.content.decode("utf-8")
        )

        sources = get_sources(results)

        print("\n")
        print("=" * 80)
        print("SOURCES USED")
        print("=" * 80)

        for source in sources:

            print(f"- {source}")

    except Exception as e:

        print(
            f"\nError: {e}"
        )
