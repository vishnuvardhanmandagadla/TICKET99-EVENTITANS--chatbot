# Dual-Brand AI Chatbot (Tickets99 + Eventitans)

RAG-powered dual-brand chatbot using **FastAPI**, **Ollama** (qwen2.5:1.5b), **ChromaDB**, and **sentence-transformers**. Each brand has its own knowledge base, personality, and embeddable frontend widget.

## How It Works

```
User types a message
        |
        v
  [Frontend Widget]  ──POST /api/ticket99/chat──>  [FastAPI Server]
        |                                                |
        |                                    ┌───────────┼───────────┐
        |                                    v           v           v
        |                              [Language    [Intent     [ChromaDB
        |                               Detection]  Classifier]  Search]
        |                               (langdetect) (keyword     (semantic
        |                                            regex)       similarity)
        |                                    |           |           |
        |                                    └───────────┼───────────┘
        |                                                v
        |                                    ┌──── [Ollama LLM] ────┐
        |                                    |    (qwen2.5:1.5b)    |
        |                                    |                      |
        |                                 SUCCESS               TIMEOUT
        |                                    |                      |
        |                                    v                      v
        |                              Natural response     Intent-based
        |                              using FAQ context    fallback response
        |                                    |                      |
        v                                    └──────────┬───────────┘
  [Display in chat bubble]  <──JSON response──  [Save to session history]
```

### The 5-Step Pipeline (rag_chain.py)

1. **Language Detection** - Detects user language (English, Hindi, Telugu, etc.) using `langdetect`
2. **Intent Classification** - Matches keywords against 20 intent categories using word-boundary regex (greeting, pricing, refund, organizer, etc.)
3. **Vector Search** - Converts message to 384-dim embedding via `all-MiniLM-L6-v2`, searches ChromaDB for top 3 most similar FAQ chunks
4. **LLM Generation** - Assembles prompt (system prompt + RAG context + intent hint + conversation history) and sends to Ollama
5. **Fallback** - If Ollama times out, returns intent-based pre-written response or best FAQ match

> See [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for a detailed flowchart with code-level explanation.

## Features

- **Dual-brand system** - Tickets99 (event ticketing) + Eventitans (event management) with separate knowledge bases
- **RAG-powered** - Retrieval-Augmented Generation using ChromaDB vector search + LLM
- **Multi-language** - Responds in Hindi, Telugu, and other languages
- **Always answers** - Falls back to intent-based responses when LLM is unavailable
- **Lead capture** - Built-in lead forms for organizers and partners
- **Embeddable widgets** - Drop a `<script>` tag on any website
- **Session memory** - Remembers conversation context (last 6 messages, 30-min TTL)
- **Scraped knowledge** - FAQ + website content from tickets99.com converted to embeddings
- **WhatsApp ready** - Webhook placeholder for WhatsApp Business API integration

## Prerequisites

- **Python 3.10+**
- **[Ollama](https://ollama.ai)** - for AI responses (chatbot works without it in fallback mode)

## Quick Start

### Option 1: Setup script (Windows)
```bat
scripts\setup.bat
scripts\start.bat
```

### Option 2: Manual setup
```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Pull the AI model (~1GB download)
ollama pull qwen2.5:1.5b

# Start the server
python main.py
```

Open **http://localhost:8000/demo** to see both chatbots side by side.

## Project Structure

```
TICKET99-EVENTITANS-chatbot/
├── backend/
│   ├── main.py                 # FastAPI server, endpoints, lifespan
│   ├── config.py               # Settings, brand configs, 20 intent definitions
│   ├── rag_chain.py            # Core RAG pipeline (detect → classify → search → LLM)
│   ├── intent_classifier.py    # Word-boundary regex keyword matching
│   ├── vector_store.py         # ChromaDB + sentence-transformers embeddings
│   ├── conversation_manager.py # In-memory session storage (30-min TTL)
│   ├── api_integrations.py     # Placeholder API integrations
│   ├── whatsapp_handler.py     # WhatsApp webhook placeholder
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment config (model, port, DB path)
│   ├── prompts/
│   │   ├── ticket99_system.txt     # Tickets99 personality + company facts
│   │   └── eventitans_system.txt   # Eventitans personality + pricing tiers
│   ├── knowledge/
│   │   ├── ticket99_faqs.json      # 59 Q&A pairs (scraped from website)
│   │   ├── eventitans_faqs.json    # 35 Q&A pairs
│   │   ├── ticket99_docs/
│   │   │   └── website_content.txt # Full scraped content from tickets99.com
│   │   └── eventitans_docs/
│   └── tests/
│       ├── test_setup.py       # Import and config validation
│       ├── test_rag.py         # Intent classifier + vector store tests
│       └── test_api.py         # API endpoint tests
├── frontend/
│   └── widgets/
│       ├── ticket99-widget.js      # Embeddable widget (orange, bottom-right)
│       ├── eventitans-widget.js    # Embeddable widget (purple, bottom-left)
│       └── widget-demo.html        # Split-screen demo page
├── scripts/
│   ├── setup.bat               # Full setup (venv + deps + model + ChromaDB)
│   ├── start.bat               # Start server
│   └── rebuild_knowledge.bat   # Rebuild ChromaDB after adding knowledge
├── HOW_IT_WORKS.md             # Detailed flowchart + code explanation
├── .gitignore
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ticket99/chat` | Chat with Tickets99 bot |
| POST | `/api/eventitans/chat` | Chat with Eventitans bot |
| POST | `/api/leads` | Submit lead form data |
| POST | `/api/clear` | Clear conversation session |
| GET | `/health` | Server + Ollama health check |
| GET | `/demo` | Demo page with both widgets |
| GET/POST | `/api/whatsapp/webhook` | WhatsApp webhook |

### Example

```bash
curl -X POST http://localhost:8000/api/ticket99/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "who founded tickets99?", "sessionId": null}'
```

```json
{
  "success": true,
  "message": "Tickets99 was founded by Siva Krishna Vangala (CEO) and Divya Somarapu (Co-Founder).",
  "sessionId": "ticket99_1234567890",
  "showForm": null,
  "brand": "ticket99"
}
```

## Embedding Widgets

Add either widget to any webpage with a single script tag:

```html
<!-- Tickets99 widget (bottom-right, orange gradient) -->
<script src="https://your-server.com/widgets/ticket99-widget.js"></script>

<!-- Eventitans widget (bottom-left, purple gradient) -->
<script src="https://your-server.com/widgets/eventitans-widget.js"></script>
```

Both widgets can run simultaneously on the same page with no conflicts.

## Updating Knowledge Base

**Add Q&A pairs:**
```json
// Add to backend/knowledge/ticket99_faqs.json
{
  "question": "Your question here?",
  "answer": "Your answer here.",
  "category": "about"
}
```

**Add documents:** Drop `.txt` files into `backend/knowledge/ticket99_docs/`

**Rebuild embeddings:**
```bat
scripts\rebuild_knowledge.bat
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Server | FastAPI + Uvicorn | Async HTTP API |
| LLM | Ollama (qwen2.5:1.5b) | Natural language generation |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) | Text → 384-dim vectors |
| Vector DB | ChromaDB | Semantic similarity search |
| Language Detection | langdetect | Multi-language support |
| Frontend | Vanilla JS (IIFE widgets) | Embeddable chat widgets |

## RAM Budget (~8GB system)

| Component | RAM Usage |
|-----------|-----------|
| Windows + background | ~3.0 GB |
| Python + FastAPI + sentence-transformers | ~300 MB |
| ChromaDB | ~200 MB |
| Ollama + qwen2.5:1.5b | ~1.0-1.5 GB |
| **Total** | **~4.5-5.0 GB** |

## Fallback Mode

If Ollama is not running or times out, the chatbot falls back gracefully:
1. **Intent match found** → Returns pre-written response for that intent (pricing, refund, greeting, etc.)
2. **No intent match** → Returns best semantic FAQ match from ChromaDB
3. **Nothing relevant** → Returns generic helpful message with website link

The bot **always responds** - it never shows an error to the user.
