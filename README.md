# Chitti — GenAI Healthcare Knowledge & Analytics Assistant

Chitti is a voice-enabled Generative AI portfolio project that combines healthcare knowledge retrieval with natural-language analytics over a synthetic healthcare database.

The goal is to explore how users can ask questions naturally, retrieve information from a knowledge base, and query structured data without writing SQL manually.

> **Project status:** Educational prototype under development. Uses demo data and is not intended for clinical decisions or production healthcare use.

## Features

- **Voice interaction:** Captures spoken questions and transcribes them using a Gemini model.
- **Speech normalization:** Uses an LLM-based step to identify likely transcription mistakes in healthcare terminology.
- **Intent routing:** Routes questions to either healthcare knowledge retrieval or structured database analytics.
- **RAG knowledge search:** Uses embeddings and ChromaDB to retrieve relevant content from the healthcare knowledge base.
- **SQL analytics:** Converts natural-language data questions into SQL for a configured MySQL database.
- **Conversation context:** Keeps recent questions and answers in the current Streamlit session to support follow-up questions.
- **Spoken responses:** Uses macOS text-to-speech through the `say` command in the current implementation.

## Architecture

```text
User asks a question by voice
              |
              v
     Gemini transcription
              |
              v
   Transcript normalization
              |
              v
       Intent router
         /       \
        /         \
       v           v
   RAG search   SQL analytics
       |           |
   ChromaDB      MySQL
       |           |
       v           v
   Knowledge     Query result
     answer         |
        \           /
         \         /
          v       v
       Answer displayed
              |
              v
       Spoken response
```

## Technology Stack

- **Language:** Python
- **User interface:** Streamlit
- **LLM and speech processing:** Google Gemini API
- **Structured response validation:** Pydantic
- **Vector database:** ChromaDB
- **Embeddings:** Gemini embedding model
- **Relational database:** MySQL
- **Data processing and generation:** Pandas and Faker

## Repository Structure

```text
chitti-healthcare-genai-assistant/
├── voice_app.py
├── healthcare_assistant.py
├── build_rag.py
├── rag_search.py
├── rag_answer.py
├── requirements.txt
├── .gitignore
├── database/
│   ├── ai_sql.py
│   ├── load_data.py
│   ├── query_database.py
│   └── test_connection.py
├── data/
│   ├── patients.csv
│   ├── clinics.csv
│   ├── doctors.csv
│   ├── appointments.csv
│   ├── treatments.csv
│   ├── treatment_stages.csv
│   ├── lab_tests.csv
│   ├── payments.csv
│   └── data-generation scripts
└── knowledge/
    └── ivf_overview.txt
```

The `vector_store/` directory is generated locally by the RAG build script and is not committed to Git.

## Getting Started

### 1. Requirements

- Python 3.11 or a compatible version
- A Google Gemini API key with access to the models used in the code
- MySQL configured with the synthetic demo tables for SQL questions
- Git

### 2. Install dependencies

Clone the repository and enter its directory:

```bash
git clone https://github.com/akanksha0206singh/chitti-healthcare-genai-assistant.git
cd chitti-healthcare-genai-assistant
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure the Gemini API key

Create `.streamlit/secrets.toml` locally with the following content:

```toml
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
```

Replace the placeholder with your own key.

**Never commit API keys, database passwords, or secrets to GitHub.** The local secrets file is excluded by `.gitignore`.

### 4. Build the knowledge index

From the project root, run:

```bash
python build_rag.py
```

This builds the local ChromaDB index from the configured knowledge source. Run it again when the source content changes.

### 5. Configure MySQL

Configure a local MySQL instance and load the synthetic demo tables using the appropriate scripts in `database/` and `data/database/`.

Review the database connection settings in those scripts before running them. Keep credentials outside the repository.

RAG questions can use the knowledge base independently of SQL analytics; database questions require a working MySQL connection and the expected schema.

### 6. Start Chitti

```bash
python -m streamlit run voice_app.py
```

Open the local URL printed by Streamlit in your browser.

## Data and Privacy

The project is intended to use synthetic demonstration data. No real patient records or confidential workplace data should be committed to this repository.

The knowledge content is educational and does not substitute for professional medical advice.

## Current Limitations

- The project is a prototype and has not been validated for clinical use.
- Retrieval quality, routing accuracy, SQL correctness, and answer grounding require systematic evaluation.
- The current spoken-response implementation uses the macOS `say` command and is not a browser-based text-to-speech solution for a hosted application.
- The SQL workflow requires a separately configured MySQL database.
- Conversation history is session-based rather than persistent application storage.
- The current interface primarily supports voice input; text input should be implemented and tested before advertising full text-and-voice interaction.
- Cloud deployment, monitoring, authentication, rate limiting, and production security hardening remain future work.

## Planned Improvements

- Build a test set to evaluate routing, retrieval, follow-up handling, and answer quality.
- Measure retrieval relevance and whether answers are supported by retrieved sources.
- Strengthen SQL safety and restrict database access to approved read-only operations.
- Add clear handling for unsupported or low-confidence questions.
- Implement browser-compatible audio playback and complete text input support.
- Prepare a secure, reproducible cloud deployment.

## Disclaimer

Chitti is an educational GenAI prototype for learning and demonstration. It is not a medical device, does not provide individualized diagnosis or treatment, and must not be used to make clinical decisions.
