from langchain_text_splitters import (
    RecursiveCharacterTextSplitter
)

from langchain_community.embeddings import (
    HuggingFaceEmbeddings
)

from langchain_community.vectorstores import (
    Chroma
)

from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader
)


DATA_DIR = "clean_docs"

DB_DIR = "chroma_db"


print("Loading documents...")

loader = DirectoryLoader(
    DATA_DIR,
    glob="*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"}
)


documents = loader.load()

print(
    f"Documents Loaded: {len(documents)}"
)


print("Creating chunks...")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)

chunks = splitter.split_documents(
    documents
)

print(
    f"Chunks Created: {len(chunks)}"
)


print(
    "\nSample Chunk:\n"
)

print(
    chunks[0].page_content[:500]
)


print(
    "\nLoading Embedding Model..."
)

embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)


print(
    "Creating Chroma Database..."
)

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    persist_directory=DB_DIR
)

vector_store.persist()

print(
    "\nDatabase Created Successfully!"
)