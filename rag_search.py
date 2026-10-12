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
# 2. Connect to ChromaDB
# -----------------------------------
chroma_client = chromadb.PersistentClient(
    path="vector_store"
)

collection = chroma_client.get_collection(
    name="healthcare_knowledge"
)


# -----------------------------------
# 3. Get user's question
# -----------------------------------
question = input("Ask your healthcare knowledge question: ").strip()

if not question:
    print("Please enter a question.")
    raise SystemExit


# -----------------------------------
# 4. Create embedding for question
# -----------------------------------
result = client.models.embed_content(
    model="gemini-embedding-2",
    contents=question,
    config=types.EmbedContentConfig(
        output_dimensionality=768
    )
)

query_embedding = result.embeddings[0].values


# -----------------------------------
# 5. Search ChromaDB
# -----------------------------------
search_results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,
    include=["documents", "metadatas", "distances"]
)


# -----------------------------------
# 6. Display retrieved chunks
# -----------------------------------
documents = search_results["documents"][0]
metadatas = search_results["metadatas"][0]
distances = search_results["distances"][0]


print("\nRetrieved knowledge:\n")

for i, document in enumerate(documents):

    print(f"--- Result {i + 1} ---")
    print(f"Source: {metadatas[i]['source']}")
    print(f"Distance: {distances[i]}")
    print(document)
    print()