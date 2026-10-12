from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import Literal
import mysql.connector
import chromadb
import os
import re
from decimal import Decimal


# =========================================================
# 1. Gemini
# =========================================================

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# =========================================================
# 2. Router structure
# =========================================================

class RouteDecision(BaseModel):
    route: Literal["sql", "rag", "unknown"]
    reason: str


# =========================================================
# 3. Database schema
# =========================================================

schema = """
patients(
    patient_id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    city,
    state,
    registration_date,
    blood_group,
    phone,
    email,
    preferred_language,
    registration_channel,
    patient_status
)

clinics(
    clinic_id,
    clinic_name,
    city,
    state,
    clinic_type,
    opening_date,
    capacity,
    status
)

doctors(
    doctor_id,
    first_name,
    last_name,
    specialization,
    experience_years,
    gender,
    clinic_id,
    joining_date,
    status
)

appointments(
    appointment_id,
    patient_id,
    doctor_id,
    clinic_id,
    appointment_date,
    booking_date,
    appointment_type,
    appointment_mode,
    reason,
    status,
    duration_minutes
)

treatments(
    treatment_id,
    patient_id,
    doctor_id,
    clinic_id,
    treatment_type,
    start_date,
    end_date,
    status,
    outcome,
    estimated_cost
)

treatment_stages(
    stage_id,
    treatment_id,
    stage_number,
    stage_name,
    stage_date,
    status
)

payments(
    payment_id,
    treatment_id,
    payment_number,
    payment_date,
    amount,
    payment_method,
    status
)

lab_tests(
    lab_test_id,
    treatment_id,
    test_name,
    test_date,
    result_value,
    unit,
    result_status,
    test_cost
)

Valid values:

Payment status:
Paid, Pending, Failed, Refunded

Treatment status:
Completed, Ongoing, Cancelled, Paused

Appointment status:
Completed, No-show, Rescheduled, Cancelled

Lab test result status:
Normal, Borderline, Abnormal
"""


# =========================================================
# 4. Conversation formatter
# =========================================================

def format_history(conversation_history):

    if not conversation_history:
        return "No previous conversation."

    lines = []

    for message in conversation_history[-6:]:

        role = message.get("role", "user")
        content = message.get("content", "")

        lines.append(
            f"{role.upper()}: {content}"
        )

    return "\n".join(lines)


# =========================================================
# 5. Router
# =========================================================

def route_question(
    question,
    conversation_history=None
):

    history = format_history(
        conversation_history or []
    )

    prompt = f"""
You are the routing system for a healthcare AI assistant.

The assistant has two information sources:

1. SQL
Use SQL when the user asks about structured records,
counts, totals, rankings, payments, appointments,
patients, treatments, doctors, clinics, or lab-test
records stored in MySQL.

SQL examples:
- How many patients are there?
- How many treatments are ongoing?
- Which clinic has the most appointments?
- How much money has been paid?
- How many abnormal lab tests are there?
- How many completed treatments are there?

2. RAG
Use RAG when the user asks about healthcare education,
medical processes, explanations, definitions, or
information contained in healthcare documents.

RAG examples:
- What are the stages of IVF?
- Explain ovarian stimulation.
- What happens during embryo transfer?
- What is IVF?
- Explain the IVF treatment process.

IMPORTANT DISTINCTION:

"IVF stages" normally means the educational stages of
the IVF process and should use RAG.

"Treatment stages" means records in the MySQL
treatment_stages table and should use SQL.

"IVF treatments" means treatment records and should
use SQL when the user asks for a count, total, status,
ranking, or other database information.

Examples:

"What are the stages of IVF?"
→ RAG

"Explain the second stage of IVF."
→ RAG

"How many IVF treatments are ongoing?"
→ SQL

"How many treatment stages are ongoing?"
→ SQL

"How many records are in treatment_stages?"
→ SQL

The user may ask follow-up questions that depend on
previous conversation.

Previous conversation:
{history}

Current question:
{question}

Use the previous conversation to understand follow-up
questions, but do not invent facts.

Classify the current question into:
sql, rag, or unknown.

Return JSON matching the required schema.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RouteDecision
        )
    )

    return RouteDecision.model_validate_json(
        response.text
    )


# =========================================================
# 6. SQL validation
# =========================================================

def validate_sql(sql_query):

    sql_query = sql_query.strip()

    sql_query = re.sub(
        r"```sql",
        "",
        sql_query,
        flags=re.IGNORECASE
    )

    sql_query = sql_query.replace(
        "```",
        ""
    ).strip()

    lower_sql = sql_query.lower()

    dangerous_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "replace",
        "grant",
        "revoke",
        "rename"
    ]

    if not re.match(
        r"^(select|with)\b",
        lower_sql
    ):
        return (
            False,
            sql_query,
            "Only SELECT/WITH queries are allowed."
        )

    if sql_query.count(";") > 1:
        return (
            False,
            sql_query,
            "Multiple SQL statements are not allowed."
        )

    if "--" in sql_query:
        return (
            False,
            sql_query,
            "SQL comments are not allowed."
        )

    if "/*" in sql_query or "*/" in sql_query:
        return (
            False,
            sql_query,
            "SQL comments are not allowed."
        )

    for word in dangerous_keywords:

        if re.search(
            r"\b" + word + r"\b",
            lower_sql
        ):
            return (
                False,
                sql_query,
                f"Blocked keyword detected: {word}"
            )

    return True, sql_query, ""


# =========================================================
# 7. SQL answer
# =========================================================


def answer_sql_question_with_password(
    question,
    mysql_password,
    conversation_history=None
):
    connection = None
    cursor = None

    try:
        mysql_host = os.getenv("MYSQL_HOST", "localhost")
        mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
        mysql_user = os.getenv("MYSQL_USER", "root")
        mysql_database = os.getenv(
            "MYSQL_DATABASE", "healthcare_ai_db"
        )
        configured_password = (
            os.getenv("MYSQL_PASSWORD") or mysql_password
        )

        connection_options = {
            "host": mysql_host,
            "port": mysql_port,
            "user": mysql_user,
            "password": configured_password,
            "database": mysql_database,
        }

        mysql_ssl_ca = os.getenv("MYSQL_SSL_CA")
        if mysql_ssl_ca:
            connection_options.update({
                "ssl_ca": mysql_ssl_ca,
                "ssl_verify_cert": True,
                "ssl_verify_identity": True,
            })

        connection = mysql.connector.connect(
            **connection_options
        )
        cursor = connection.cursor()

        history = format_history(
            conversation_history or []
        )

        prompt = f"""
You are a MySQL SQL assistant for a healthcare analytics system.

Database schema:
{schema}

Previous conversation:
{history}

Current user question:
{question}

Generate ONE read-only MySQL query.

IMPORTANT MEANING RULES:

1. "IVF stages" normally means educational IVF stages
   and should be handled by RAG.
2. "Treatment stages" means records in treatment_stages.
3. "IVF treatments" means records in treatments when
   asking about counts, status, totals, or rankings.
4. Do not confuse educational stages, treatment records,
   and treatment_stages records.
5. Never invent tables or columns.
6. Never invent categorical values.
7. Treatment statuses: Completed, Ongoing, Cancelled, Paused.
8. Payment statuses: Paid, Pending, Failed, Refunded.
9. Appointment statuses: Completed, No-show,
   Rescheduled, Cancelled.
10. Lab-test result statuses: Normal, Borderline, Abnormal.
11. Use only tables and columns in the schema.
12. Use valid MySQL syntax.
13. Generate exactly ONE SELECT query.
14. Never generate INSERT, UPDATE, DELETE, DROP, ALTER,
    TRUNCATE, CREATE, REPLACE, GRANT, REVOKE, or RENAME.
15. Use previous conversation only to understand context.

Return SQL only. Do not include explanations.
"""

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        sql_query = (response.text or "").strip()

        safe, sql_query, error = validate_sql(sql_query)

        if not safe:
            return f"SQL blocked: {error}"

        cursor.execute(sql_query)
        results = cursor.fetchall()

        if not results:
            return "No matching data was found."

        first_row = results[0]

        if len(first_row) == 1:
            value = first_row[0]

            if value is None:
                return "No matching data was found."

            if isinstance(value, Decimal):
                return f"₹{value:,.2f}"

            if isinstance(value, (int, float)):
                return f"{value:,}"

            return str(value)

        if len(first_row) == 2:
            name, value = first_row

            if value is None:
                return f"{name}: no matching data was found."

            if isinstance(value, Decimal):
                return f"{name}: ₹{value:,.2f}"

            if isinstance(value, (int, float)):
                return f"{name}: {value:,}"

            return f"{name}: {value}"

        if len(first_row) == 3:
            first, second, third = first_row

            if isinstance(third, Decimal):
                return f"{second} ({first}): ₹{third:,.2f}"

            if isinstance(third, (int, float)):
                return f"{second} ({first}) has {third:,}."

            return f"{second} ({first}): {third}"

        return "\n".join(
            str(row) for row in results[:10]
        )

    except mysql.connector.Error as error:
        return f"MySQL error: {error}"

    finally:
        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()
# =========================================================
# 8. RAG answer with relevance checking and source citations
# =========================================================

def answer_rag_question_for_app(
    question,
    conversation_history=None
):
    # 1. Connect to ChromaDB
    chroma_client = chromadb.PersistentClient(
        path="vector_store"
    )

    collection = chroma_client.get_collection(
        name="healthcare_knowledge"
    )

    total_chunks = collection.count()

    if total_chunks == 0:
        return "The knowledge base is empty."

    # 2. Prepare conversation history
    history = format_history(
        conversation_history or []
    )

    # Improve retrieval for short follow-up questions
    follow_up_pattern = (
        r"\b(it|that|those|them|first|second|third|"
        r"next|previous|same|above)\b"
    )

    if (
        conversation_history
        and re.search(
            follow_up_pattern,
            question,
            re.IGNORECASE
        )
    ):
        retrieval_query = (
            f"Current question: {question}\n"
            f"Conversation context: {history}"
        )
    else:
        retrieval_query = question

    # 3. Convert question into an embedding
    embedding_response = client.models.embed_content(
        model="gemini-embedding-2",
        contents=retrieval_query,
        config=types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    query_embedding = (
        embedding_response.embeddings[0].values
    )

    # 4. Retrieve the five closest matches
    result_count = min(5, total_chunks)

    search_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=result_count,
        include=[
            "documents",
            "metadatas",
            "distances"
        ]
    )

    documents = search_results["documents"][0]
    metadatas = search_results["metadatas"][0]
    distances = search_results["distances"][0]

    retrieved_chunks = list(
        zip(documents, metadatas, distances)
    )

    if not retrieved_chunks:
        return (
            "I couldn't find relevant information "
            "in the knowledge base."
        )

    # 5. Initial relevance check
    # Lower squared-L2 distance means a closer vector match.
    # This threshold is provisional and should be tested
    # against relevant and irrelevant questions.
    MAX_DISTANCE = 0.85

    best_distance = min(
        float(item[2])
        for item in retrieved_chunks
    )

    if best_distance > MAX_DISTANCE:
        return (
            "I couldn't find sufficiently relevant "
            "information in my knowledge base to answer "
            "that question."
        )

    relevant_chunks = [
        item
        for item in retrieved_chunks
        if float(item[2]) <= MAX_DISTANCE
    ]

    if not relevant_chunks:
        return (
            "I couldn't find enough relevant information "
            "in the knowledge base."
        )

    # 6. Detect questions asking for a complete process/list
    broad_question_pattern = (
        r"\b(stages?|steps?|process|overview|"
        r"list|all|sequence|complete)\b"
    )

    is_broad_question = bool(
        re.search(
            broad_question_pattern,
            question,
            re.IGNORECASE
        )
    )

    # 7. Broad questions: retrieve the complete relevant
    # source document so lists are not accidentally truncated.
    if is_broad_question:

        relevant_sources = list(dict.fromkeys(
            metadata.get("source", "")
            for document, metadata, distance
            in relevant_chunks
            if metadata.get("source")
        ))

        all_source_chunks = []

        for source in relevant_sources:

            source_records = collection.get(
                where={"source": source},
                include=[
                    "documents",
                    "metadatas"
                ]
            )

            source_documents = (
                source_records["documents"] or []
            )

            source_metadatas = (
                source_records["metadatas"] or []
            )

            for document, metadata in zip(
                source_documents,
                source_metadatas
            ):
                all_source_chunks.append(
                    (document, metadata)
                )

        all_source_chunks.sort(
            key=lambda item: (
                item[1].get("source", ""),
                item[1].get("chunk_index", 999999)
            )
        )

        context_chunks = all_source_chunks

    else:
        # Specific questions: use the most relevant chunks.
        relevant_chunks.sort(
            key=lambda item: float(item[2])
        )

        context_chunks = [
            (document, metadata)
            for document, metadata, distance
            in relevant_chunks
        ]

    if not context_chunks:
        return (
            "I couldn't find enough relevant information "
            "in the knowledge base to answer that question."
        )

    # 8. Build context and collect source information
    context_parts = []
    sources_used = {}

    for document, metadata in context_chunks:

        source = metadata.get(
            "source",
            "Unknown source"
        )

        topic = metadata.get(
            "topic",
            "General"
        )

        sources_used[source] = topic

        context_parts.append(
            f"[Source: {source}; Topic: {topic}]\n"
            f"{document}"
        )

    context = "\n\n".join(context_parts)

    # 9. Generate an evidence-grounded answer
    prompt = f"""
You are Chitti, a healthcare knowledge assistant.

Answer the user's current question using the
provided knowledge-base context.

Previous conversation:
{history}

Current question:
{question}

Retrieved knowledge:
{context}

Rules:
- Use only information supported by the context.
- If the context does not answer the question, say so.
- Do not invent medical facts or sources.
- Do not diagnose or provide personalized medical advice.
- For questions asking for all stages or steps, include
  every relevant step present in the context.
- Preserve the original order of numbered stages.
- Use previous conversation to understand follow-ups,
  not as a substitute for supporting evidence.
- Do not invent source citations; the app displays
  the retrieved source filenames separately.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    answer = (response.text or "").strip()
    if not answer:
        answer = (
            "I couldn't generate an answer from the "
            "retrieved knowledge."
        )

    # Check whether the knowledge base could answer
    lower_answer = answer.lower()

    unsupported_markers = [
        "no information available",
        "don't have enough information",
        "do not have enough information",
        "not enough information",
        "does not contain enough information",
        "doesn't contain enough information",
        "no mention of",
        "not covered in the knowledge base",
        "couldn't find relevant information",
        "couldn't find sufficiently relevant information"
    ]

    if any(
        marker in lower_answer
        for marker in unsupported_markers
    ):
        return answer

    # Add source citations
    source_lines = []

    for source, topic in sorted(sources_used.items()):
        source_lines.append(
            f"- `{source}` — {topic}"
        )

    if source_lines:
        answer += (
            "\n\n**Sources used:**\n"
            + "\n".join(source_lines)
        )

    return answer
# =========================================================
# 9. Command-line mode
# =========================================================

if __name__ == "__main__":

    print("=" * 55)
    print("Healthcare AI Assistant")
    print("=" * 55)

    conversation_history = []

    while True:

        question = input(
            "\nAsk your healthcare question "
            "(type 'exit' to quit): "
        ).strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        try:

            decision = route_question(
                question,
                conversation_history
            )

            print(
                f"\nRoute: {decision.route}"
            )

            if decision.route == "sql":

                password = input(
                    "Enter your MySQL password: "
                )

                answer = (
                    answer_sql_question_with_password(
                        question,
                        password,
                        conversation_history
                    )
                )

            elif decision.route == "rag":

                answer = (
                    answer_rag_question_for_app(
                        question,
                        conversation_history
                    )
                )

            else:

                answer = (
                    "I can answer questions about the "
                    "healthcare database and the available "
                    "healthcare knowledge."
                )

            print("\nAnswer:")
            print(answer)

            conversation_history.append({
                "role": "user",
                "content": question
            })

            conversation_history.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as error:

            print(
                f"\nAssistant error: {error}"
            )