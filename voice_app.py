import subprocess
import sys
import os
import tempfile
import subprocess

import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel

# Configure the page before other Streamlit operations
st.set_page_config(
    page_title="Chitti",
    page_icon="🎙️"
)

# Load Gemini API key before importing healthcare_assistant
try:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# Import healthcare assistant functions
from healthcare_assistant import (
    route_question,
    answer_sql_question_with_password,
    answer_rag_question_for_app
)

@st.cache_resource
def ensure_rag_index():
    import chromadb

    chroma_client = chromadb.PersistentClient(
        path="vector_store"
    )

    try:
        collection = chroma_client.get_collection(
            name="healthcare_knowledge"
        )
        if collection.count() > 0:
            return
    except Exception:
        pass

    with st.spinner(
        "Preparing Chitti's healthcare knowledge base..."
    ):
        result = subprocess.run(
            [sys.executable, "build_rag.py"],
            capture_output=True,
            text=True
        )

    if result.returncode != 0:
        st.error(
            "Could not prepare the knowledge base. "
            "Check the Gemini API key and app logs."
        )
        if result.stderr:
            st.code(result.stderr[-2000:])
        st.stop()


ensure_rag_index()

# =========================================================
# Chitti UI styling
# =========================================================

st.markdown("""
<style>
    .stApp {
        background: #f4f7fb;
        color: #172033;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }

    h1, h2, h3 {
        color: #172033;
        letter-spacing: -0.4px;
    }

    .chitti-hero {
        background: linear-gradient(125deg, #101827 0%, #164e63 100%);
        border-radius: 24px;
        padding: 32px;
        margin-bottom: 26px;
        color: white;
        border: 1px solid rgba(255,255,255,0.12);
    }

    .chitti-label {
        color: #7dd3c7;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }

    .chitti-title {
        font-size: 40px;
        font-weight: 750;
        color: white;
        line-height: 1.15;
        margin-bottom: 10px;
    }

    .chitti-subtitle {
        font-size: 16px;
        color: #d5e6ef;
        line-height: 1.6;
        max-width: 650px;
    }

    .chitti-tags {
        margin-top: 20px;
    }

    .chitti-tag {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 20px;
        margin: 4px 5px 0 0;
        background: rgba(255,255,255,0.10);
        border: 1px solid rgba(255,255,255,0.18);
        color: #e4f4f5;
        font-size: 11px;
        letter-spacing: 0.5px;
    }

    [data-testid="stChatMessage"] {
        background: white;
        border: 1px solid #e4eaf2;
        border-radius: 18px;
        padding: 16px;
        margin: 12px 0;
        box-shadow: 0 3px 12px rgba(25, 45, 75, 0.035);
    }

    [data-testid="stAudioInput"] {
        background: white;
        padding: 14px;
        border: 1px solid #dfe7f0;
        border-radius: 16px;
    }

    .stButton > button {
        border-radius: 12px;
        border: 1px solid #dce5ef;
        font-weight: 600;
        transition: all 0.15s ease;
    }

    .stButton > button:hover {
        border-color: #0f766e;
        color: #0f766e;
    }

    [data-testid="stSidebar"] {
        background: #101827;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: #edf3fa;
    }

    div[data-testid="stAlert"] {
        border-radius: 14px;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
</style>
""", unsafe_allow_html=True)



st.html("""
<div class="chitti-hero">
    <div class="chitti-label">
        YOUR HEALTHCARE AI ASSISTANT
    </div>

    <div class="chitti-title">
        Meet Chitti.
    </div>

    <div class="chitti-subtitle">
        Ask questions naturally. Explore healthcare knowledge,
        understand processes, and query your synthetic analytics
        database using voice or text.
    </div>

    <div class="chitti-tags">
        <span class="chitti-tag">VOICE ASSISTANT</span>
        <span class="chitti-tag">SQL ANALYTICS</span>
        <span class="chitti-tag">RAG KNOWLEDGE SEARCH</span>
    </div>
</div>
""")
# =========================================================
# 2. Session state
# =========================================================

if "conversation" not in st.session_state:
    st.session_state.conversation = []

if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None


# =========================================================
# 3. Gemini API
# =========================================================

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error(
        "Gemini API key not found. "
        "Check .streamlit/secrets.toml."
    )
    st.stop()

client = genai.Client(
    api_key=api_key
)


# =========================================================
# 4. Transcript normalization structure
# =========================================================

class NormalizationDecision(BaseModel):
    normalized_question: str
    changed: bool
    confidence: int
    reason: str


# =========================================================
# 5. Normalize speech-recognition mistakes
# =========================================================

def normalize_transcript(
    transcript,
    conversation_history
):

    history_text = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in conversation_history[-6:]
    )

    if not history_text:
        history_text = "No previous conversation."

    prompt = f"""
You are a healthcare speech-recognition normalization assistant.

The following text came from automatic speech recognition.
It may contain pronunciation-related transcription errors,
especially with healthcare terms and acronyms.

Current transcript:
{transcript}

Previous conversation:
{history_text}

Healthcare vocabulary that may appear:
IVF
in vitro fertilization
embryo
embryo transfer
ovarian stimulation
egg retrieval
fertilization
fertility
pregnancy testing
treatment
treatment stages
patient
clinic
doctor
appointment
lab test
payment
IBS

Your task:

1. Decide whether the transcript contains a likely
   speech-recognition error.

2. Use the complete sentence and conversation context.

3. Correct a term ONLY when the intended meaning is highly
   likely.

4. Do NOT automatically change one legitimate medical term
   into another.

5. For example:
   "What are the stages of IPS?"
   may plausibly mean IVF if the surrounding context clearly
   indicates IVF.

6. But:
   "What are the symptoms of IBS?"
   should remain IBS.

7. Do not invent a new question.

8. Preserve the user's intended meaning.

9. If no correction is needed, return the original transcript.

10. confidence must be between 0 and 100.

Return JSON matching the required schema.
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=NormalizationDecision
        )
    )

    try:
        return NormalizationDecision.model_validate_json(
            response.text
        )
    except Exception:

        return NormalizationDecision(
            normalized_question=transcript,
            changed=False,
            confidence=100,
            reason="Normalization result could not be parsed."
        )


# =========================================================
# 6. MySQL password
# =========================================================

mysql_password = st.text_input(
    "MySQL password "
    "(only needed for database questions)",
    type="password"
)


# =========================================================
# 7. Display conversation history
# =========================================================

for message in st.session_state.conversation:

    with st.chat_message(
        message["role"]
    ):

        st.write(
            message["content"]
        )


# =========================================================
# 8. Voice input
# =========================================================

audio = st.audio_input(
    "Record your question"
)


# =========================================================
# 9. Process audio
# =========================================================

# =========================================================
# 9. Process audio
# =========================================================

if audio:

    audio_id = str(
        hash(audio.getvalue())
    )

    # Prevent processing the same recording repeatedly
    if audio_id == st.session_state.last_audio_id:
        st.stop()

    st.audio(
        audio,
        format="audio/wav"
    )

    audio_path = None

    try:

        # -------------------------------------------------
        # Save microphone audio temporarily
        # -------------------------------------------------

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as temp_file:

            temp_file.write(
                audio.getvalue()
            )

            audio_path = temp_file.name


        # -------------------------------------------------
        # Speech-to-text
        # -------------------------------------------------

        with st.spinner(
            "Understanding your voice..."
        ):

            audio_file = client.files.upload(
                file=audio_path
            )

            interaction = client.interactions.create(
                model="gemini-3.5-transcribe",
                input=[
                    {
                        "type": "audio",
                        "uri": audio_file.uri,
                        "mime_type": (
                            audio_file.mime_type
                            or "audio/wav"
                        )
                    }
                ],
                generation_config={
                    "transcription_config": {
                        "mode": "smart",
                        "custom_vocabulary": [
                            "IVF",
                            "in vitro fertilization",
                            "embryo",
                            "embryo transfer",
                            "ovarian stimulation",
                            "egg retrieval",
                            "fertilization",
                            "fertility",
                            "pregnancy testing",
                            "treatment stages",
                            "IBS"
                        ]
                    }
                }
            )

            transcript = (
                interaction.output_text
                or ""
            ).strip()


        # -------------------------------------------------
        # Check transcription
        # -------------------------------------------------

        if not transcript:

            st.error(
                "I could not understand the recording. "
                "Please try again."
            )

            st.stop()


        # -------------------------------------------------
        # Show raw transcription
        # -------------------------------------------------

        st.subheader("You said:")

        st.write(
            transcript
        )


        # -------------------------------------------------
        # Normalize possible ASR errors
        # -------------------------------------------------

        with st.spinner(
            "Checking healthcare terminology..."
        ):

            normalization = normalize_transcript(
                transcript,
                st.session_state.conversation
            )


        normalized_question = (
            normalization.normalized_question.strip()
        )


        # -------------------------------------------------
        # Decide which question goes to the assistant
        # -------------------------------------------------

        if (
            normalization.changed
            and normalization.confidence >= 90
            and normalized_question
        ):

            question_for_assistant = (
                normalized_question
            )

            st.info(
                f"Understood as: {normalized_question}"
            )

            st.caption(
                f"Normalization confidence: "
                f"{normalization.confidence}%"
            )

        else:

            question_for_assistant = transcript


        # -------------------------------------------------
        # Route SQL vs RAG
        # -------------------------------------------------

        with st.spinner(
            "Understanding your question..."
        ):

            decision = route_question(
                question_for_assistant,
                st.session_state.conversation
            )


        st.caption(
            f"Detected route: {decision.route}"
        )


        # =================================================
        # SQL ROUTE
        # =================================================

        if decision.route == "sql":

            if not mysql_password:

                st.warning(
                    "This question needs database access. "
                    "Enter your MySQL password above."
                )

                st.stop()


            with st.spinner(
                "Querying the healthcare database..."
            ):

                answer = (
                    answer_sql_question_with_password(
                        question_for_assistant,
                        mysql_password,
                        st.session_state.conversation
                    )
                )


        # =================================================
        # RAG ROUTE
        # =================================================

        elif decision.route == "rag":

            with st.spinner(
                "Searching the healthcare knowledge base..."
            ):

                answer = (
                    answer_rag_question_for_app(
                        question_for_assistant,
                        st.session_state.conversation
                    )
                )


        # =================================================
        # UNKNOWN ROUTE
        # =================================================

        else:

            answer = (
                "I can answer questions about the "
                "healthcare database and the available "
                "healthcare knowledge."
            )


        # =================================================
        # Display answer
        # =================================================

        st.subheader("AI answer:")

        st.write(
            answer
        )


        # =================================================
        # Save conversation
        # =================================================

        st.session_state.conversation.append(
            {
                "role": "user",
                "content": question_for_assistant
            }
        )

        st.session_state.conversation.append(
            {
                "role": "assistant",
                "content": answer
            }
        )
        st.session_state.last_audio_id = audio_id

        # =================================================
        # Text-to-speech
        # =================================================

        try:

            subprocess.Popen(
                [
                    "say",
                    str(answer)
                ]
            )

        except Exception:

            pass


    except Exception as error:

        st.error(
            f"Assistant error: {error}"
        )


    finally:

        if audio_path:

            try:
                os.remove(
                    audio_path
                )
            except Exception:
                pass