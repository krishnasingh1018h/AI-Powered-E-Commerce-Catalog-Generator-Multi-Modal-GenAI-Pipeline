AI-Powered E-Commerce Catalog Generator

An enterprise-grade, multi-modal GenAI cataloging pipeline that automates the transformation of raw product apparel imagery into structured, SEO-optimized marketplace listings. This project employs a decoupled architecture combining a **FastAPI backend microservice**, a **Streamlit frontend dashboard**, and a **Two-Stage LLM extraction workflow** to strike a perfect balance between high-performance cloud vision capabilities and cost-effective, deterministic local text structuring.

---

🏗️ System Architecture & Deep Dive
Unlike typical single-prompt multi-modal pipelines that suffer from frequent formatting hallucinations, high API costs, and payload timeout failures, this system decouples visual extraction from structural formatting:

```
                      ┌──────────────────────────────┐
                      │    Streamlit UI (app_ui.py)  │
                      └──────────────┬───────────────┘
                                     │ (Multipart Image Upload)
                                     ▼
                      ┌──────────────────────────────┐
                      │     FastAPI API (api.py)     │
                      └──────────────┬───────────────┘
                                     │
             ┌───────────────────────┴───────────────────────┐
             ▼ [Stage 1: Multi-Modal Vision]                 ▼ [Stage 2: Schema Structuring]
┌─────────────────────────────────────────┐     ┌─────────────────────────────────────────┐
│              Groq Cloud API             │     │              Huggingface API               │
│     (Llama 4 Scout 17B MoE Instruct)    │     │           (Qwen2.5 7B Instruct)         │
├─────────────────────────────────────────┤     ├─────────────────────────────────────────┤
│ • Parses high-res image inputs          │     │ • Receives raw text narrative specs     │
│ • Runs custom human-model masking filter │     │ • Hydrates LangChain Pydantic structure │
│ • Generates raw text descriptive layout │     │ • Emits guaranteed, zero-hallucination │
│   (fabric, draping, patterns, styling)  │     │   JSON schemas for marketplace APIs     │
└───────────────────┬─────────────────────┘     └───────────────────▲─────────────────────┘
                    │                                               │
                    └───────────────[Plain Text Visual Specs]───────┘

```

Stage 1: Cloud Vision Pipeline (Groq)

The image payload is routed to Meta's **Llama 4 Scout (17B)** via Groq's high-speed LPU infrastructure. The vision prompt utilizes a strict behavioral boundary mask to bypass human models:

> *"CRITICAL INSTRUCTION: You are analyzing a garment worn by a human model. Ignore the human model entirely. Do not mention their hair, skin, pose, accessories, or the background. Focus strictly on the structural and visual details of the primary apparel item being showcased."*

Stage 2: Local Structured Hydration (Ollama)

The raw descriptive output string from Stage 1 is bridged directly into a localized **Qwen2.5 (7B)** instance managed via LangChain. This step enforces absolute structural determinism through Pydantic schemas, bypassing expensive cloud text processing while locking down marketplace-compliant payloads.

---
⚡ Key Features

* **Advanced Multi-Modal Processing:** Instantly translates visual fashion attributes (necklines, sleeve patterns, fabric types, dress silhouettes) into copywriter text blocks.
* **On-the-Fly Image Compression:** Uses Pillow to dynamically downscale large modern smartphone images ($>1200\text{px}$) and compress them to JPEG quality 80 in-memory. This cuts payload footprint down from up to 10MB to less than 600KB, permanently avoiding cloud `413 Request Entity Too Large` errors.
* **Modern Responsive Streamlit Dashboard:** Upgraded UI layers utilizing Streamlit's new `width="stretch"` layout specs across previews and generation triggers to maximize horizontal real estate.
* **Platform-Targeted SEO:** Generates tailored titles, descriptions, and tag models fine-tuned to comply with the listing algorithms of platforms like **Meesho, Amazon, and Myntra**.

---

📂 Repository Blueprint
├── .env                    # Local environment variables (excluded from version control)
├── .gitattributes          # Enforces Linux-friendly (LF) line endings for shell scripts
├── .gitignore              # Excludes virtual environments (venv), .env, and __pycache__
├── Dockerfile              # Containerization instructions for isolated deployment
├── requirement.txt         # Project dependencies and library versions
├── start.sh                # Multi-service bash initialization and automation script
├── test.py                 # Local testing scripts for pipeline validation
└── model/                  # Core application directory
    ├── api.py              # FastAPI service exposing endpoints and in-memory image compression
    ├── app.py              # Streamlit responsive frontend control panel
    ├── main.py             # Global orchestration layer (LangChain & Hugging Face setup)
    └── schema.py           # Pydantic data models enforcing structured JSON outputs

---

🛠️ Setup & Installation

1. Environment Configurations

Clone the repository, create a python virtual environment, and install your dependencies:

```bash
pip install fastapi uvicorn streamlit langchain langchain-openai langchain-Huggingface pillow requests pydantic python-dotenv
```

3. Handle Environment Keys

Generate a free API key inside your [Groq Cloud Console](https://console.groq.com/). Create a `.env` file directly within your root directory:
Generate a free API key inside your Huggingface . Create a `.env` file directly within your root directory:
```text
GROQ_API_KEY=gsk_your_production_secret_key_here
HUGGINGFACE_API_KEY=you_secret_key
```

4. Run the Architecture

You can instantly deploy both microservices concurrently using the provided automated startup script:

```bash
chmod +x start.sh
./start.sh

```

*Alternatively, you can open a terminal split and spin up each module manually:*

**FastAPI Backend Execution:**
```bash
uvicorn model.api:app --host 127.0.0.1 --port 8000 --reload

```


**Streamlit UI Interface Execution:**
```bash
streamlit run model/app_ui.py

```



---

## 📑 Core API Contract Documentation

### Post Route: Image Feature Extraction

* **Endpoint:** `POST [http://127.0.0.1:8000/generate-image](http://127.0.0.1:8000/generate-image)`
* **Payload Format:** `multipart/form-data`
* **Form Parameters:** `file: [Raw Binary Image Blob]`

#### Response Payload (Enforced Pydantic Schema Output):

```json
{
  "product_title": "Women's Navy Blue Cotton Embroidered A-line Kurti",
  "description_bullets": [
    "Premium breathable cotton fabric engineered for all-day comfort",
    "Intricate white traditional geometric embroidery framing the round neck design",
    "Flattering structural A-line silhouette with classic 3/4 sleeves"
  ],
  "seo_keywords": [
    "navy blue kurti",
    "cotton embroidered kurti",
    "meesho catalog kurtas",
    "ethnic summer wear"
  ]
}

```
