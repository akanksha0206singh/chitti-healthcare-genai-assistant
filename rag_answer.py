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
# 3. Get user question
# -----------------------------------
question = input(
    "Ask your healthcare knowledge question: "
).strip()

if not question:
    print("Please enter a question.")
    raise SystemExit


# -----------------------------------
# 4. Create question embedding
# -----------------------------------
embedding_response = client.models.embed_content(
    model="gemini-embedding-2",
    contents=question,
    config=types.EmbedContentConfig(
        output_dimensionality=768
    )
)

query_embedding = (
    embedding_response.embeddings[0].values
)


# -----------------------------------
# 5. Search ChromaDB
# -----------------------------------
search_results = collection.query(
    query_embeddings=[query_embedding],
    n_results=13,
    include=[
        "documents",
        "metadatas",
        "distances"
    ]
)


# -----------------------------------
# 6. Retrieve documents
# -----------------------------------
documents = search_results["documents"][0]
metadatas = search_results["metadatas"][0]


# -----------------------------------
# 7. Put chunks back into
#    original document order
# -----------------------------------
retrieved_chunks = list(
    zip(documents, metadatas)
)

retrieved_chunks.sort(
    key=lambda item: item[1]["chunk_index"]
)


# -----------------------------------
# 8. Build context
# -----------------------------------
context_parts = []

for document, metadata in retrieved_chunks:

    context_parts.append(
        document
    )

context = "\n\n".join(context_parts)


# -----------------------------------
# 9. Ask Gemini to answer
# -----------------------------------
answer_prompt = f"""
You are a healthcare knowledge assistant.

Answer the user's question using ONLY the
information contained in the context.

User question:
{question}

Context:
{context}

Instructions:
- Read the complete context before answering.
- Preserve the original order of numbered stages.
- If the context contains numbered stages, list them in
  their correct numerical order.
- Do not invent or add information.
- Do not skip relevant stages.
- Keep the answer clear and concise.
- Do not provide diagnosis or personalized medical advice.
- If the information is not available in the context,
  say:
  "I don't have enough information in my knowledge base
  to answer that."
"""

answer_response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents=answer_prompt
)


# -----------------------------------
# 10. Display answer
# -----------------------------------
print("\nAI answer:")
print(answer_response.text)