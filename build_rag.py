from google import genai
from google.genai import types
import chromadb
import os


# -----------------------------------
# 1. Connect to Gemini
# -----------------------------------
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# -----------------------------------
# 2. Read knowledge document
# -----------------------------------
with open(
    "knowledge/ivf_overview.txt",
    "r",
    encoding="utf-8"
) as file:
    document = file.read()


# -----------------------------------
# 3. Split document into chunks
# -----------------------------------
chunks = [
    chunk.strip()
    for chunk in document.split("\n\n")
    if chunk.strip()
]


print(f"Loaded {len(chunks)} knowledge chunks.")


# -----------------------------------
# 4. Create embeddings
# -----------------------------------
embeddings = []

for chunk in chunks:

    result = client.models.embed_content(
        model="gemini-embedding-2",
        contents=chunk,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    embeddings.append(
        result.embeddings[0].values
    )


print("Embeddings created successfully.")


# -----------------------------------
# 5. Connect to ChromaDB
# -----------------------------------
chroma_client = chromadb.PersistentClient(
    path="vector_store"
)


# -----------------------------------
# 6. Create / load collection
# -----------------------------------
collection = chroma_client.get_or_create_collection(
    name="healthcare_knowledge"
)


# -----------------------------------
# 7. Store metadata including order
# -----------------------------------
ids = [
    f"ivf_chunk_{i}"
    for i in range(len(chunks))
]

metadatas = [
    {
        "source": "ivf_overview.txt",
        "topic": "IVF",
        "chunk_index": i
    }
    for i in range(len(chunks))
]


# -----------------------------------
# 8. Store in ChromaDB
# -----------------------------------
collection.upsert(
    ids=ids,
    documents=chunks,
    embeddings=embeddings,
    metadatas=metadatas
)


print("Knowledge stored in ChromaDB successfully.")
print("Total documents in collection:", collection.count())