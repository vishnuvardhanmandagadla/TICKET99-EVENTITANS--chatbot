# How the Chatbot Answers Questions

## Complete Flow Chart

```
 USER TYPES A MESSAGE (e.g. "how much does it cost?")
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: FRONTEND WIDGET  (ticket99-widget.js / eventitans-widget.js)  │
│                                                                 │
│  • User types message in the chat input box                     │
│  • Widget shows typing indicator (bouncing dots)                │
│  • Sends HTTP POST request to backend:                          │
│      POST /api/ticket99/chat                                    │
│      Body: { "message": "how much does it cost?",               │
│              "sessionId": "ticket99_1234567890" }                │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: FASTAPI SERVER  (main.py → _handle_chat)              │
│                                                                 │
│  • Receives the request                                         │
│  • Extracts message + sessionId from JSON body                  │
│  • Creates or retrieves session (conversation_manager.py)       │
│  • Saves user message to session history                        │
│  • Calls: generate_response(brand, message, session_id)         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: RAG PIPELINE  (rag_chain.py → generate_response)      │
│                                                                 │
│  This is where the magic happens. 4 sub-steps run in sequence:  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  3A. LANGUAGE DETECTION  (langdetect library)             │  │
│  │                                                           │  │
│  │  Input:  "how much does it cost?"                         │  │
│  │  Output: "en" (English)                                   │  │
│  │                                                           │  │
│  │  Input:  "telugu lo cheppu"                               │  │
│  │  Output: "te" (Telugu)                                    │  │
│  │                                                           │  │
│  │  • Uses Google's langdetect library                       │  │
│  │  • If language ≠ English, adds instruction to the LLM     │  │
│  │    prompt: "Respond in the same language"                  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  3B. INTENT CLASSIFICATION  (intent_classifier.py)        │  │
│  │                                                           │  │
│  │  Input:  "how much does it cost?"                         │  │
│  │  Output: ("pricing", 0.90)                                │  │
│  │                                                           │  │
│  │  HOW IT WORKS:                                            │  │
│  │  1. Lowercases the message, strips punctuation            │  │
│  │  2. Loops through 20 intent categories in priority order: │  │
│  │     greeting → farewell → gratitude → refund → cancel     │  │
│  │     → pricing → organizer → attendee → partnership        │  │
│  │     → support → contact → features → about → payment     │  │
│  │     → checkin → analytics → security → getting_started    │  │
│  │     → cities → discount                                   │  │
│  │  3. For each intent, checks keyword list:                 │  │
│  │     • Single words: word-boundary regex (\brate\b)        │  │
│  │       prevents "rate" matching inside "integrate"         │  │
│  │     • Multi-word phrases: substring match                 │  │
│  │       "how much" found inside "how much does it cost"     │  │
│  │  4. Returns FIRST match (priority ordering matters)       │  │
│  │  5. If nothing matches → returns (None, 0.0)              │  │
│  │                                                           │  │
│  │  EXAMPLE - "I want a refund":                             │  │
│  │    greeting keywords? No                                  │  │
│  │    farewell keywords? No                                  │  │
│  │    gratitude keywords? No                                 │  │
│  │    refund keywords? "refund" ← MATCH! → ("refund", 0.94) │  │
│  └───────────────────────────────────────────────────────────┘  │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  3C. VECTOR SEARCH  (vector_store.py → ChromaDB)          │  │
│  │                                                           │  │
│  │  Input:  "how much does it cost?"                         │  │
│  │  Output: Top 3 most relevant FAQ chunks                   │  │
│  │                                                           │  │
│  │  HOW IT WORKS:                                            │  │
│  │  1. Converts user message → 384-dim vector embedding      │  │
│  │     using sentence-transformers (all-MiniLM-L6-v2)        │  │
│  │  2. Searches the brand's ChromaDB collection:             │  │
│  │     • ticket99_knowledge (45 FAQ chunks)                  │  │
│  │     • eventitans_knowledge (35 FAQ chunks)                │  │
│  │  3. Returns top 3 matches with cosine distance            │  │
│  │  4. FILTERS OUT chunks with distance > 1.5 (irrelevant)  │  │
│  │                                                           │  │
│  │  EXAMPLE RESULT:                                          │  │
│  │  [                                                        │  │
│  │    { distance: 0.42,                                      │  │
│  │      question: "What is the pricing for Tickets99?",      │  │
│  │      answer: "Free to list, 2-5% commission..." },        │  │
│  │    { distance: 0.68,                                      │  │
│  │      question: "Is there any cost to create account?",    │  │
│  │      answer: "No! Creating an account is free..." },      │  │
│  │    { distance: 0.91,                                      │  │
│  │      question: "What are payment processing fees?",       │  │
│  │      answer: "Payment processing is 2% + GST..." }       │  │
│  │  ]                                                        │  │
│  │                                                           │  │
│  │  WHAT IS ChromaDB?                                        │  │
│  │  A vector database that stores FAQ text as mathematical   │  │
│  │  vectors. When you search "how much does it cost?", it    │  │
│  │  finds FAQs with SIMILAR MEANING, not just matching       │  │
│  │  words. "cost" finds "pricing" and "fees" too.            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                      │                                          │
│                      ▼                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  3D. PROMPT ASSEMBLY + LLM CALL  (rag_chain.py)           │  │
│  │                                                           │  │
│  │  Builds a prompt for Ollama (phi3:mini) with 5 parts:     │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │ PART 1: System Prompt (from prompts/ticket99_system │  │  │
│  │  │         .txt or eventitans_system.txt)              │  │  │
│  │  │                                                     │  │  │
│  │  │ "You are the Tickets99 AI assistant..."             │  │  │
│  │  │ Company facts, personality rules, response limits   │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │ PART 2: RAG Context (from ChromaDB search above)    │  │  │
│  │  │                                                     │  │  │
│  │  │ "Relevant information from our knowledge base:      │  │  │
│  │  │  1. Q: What is the pricing?                         │  │  │
│  │  │     A: Free to list, 2-5% commission..."            │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │ PART 3: Intent Hint                                 │  │  │
│  │  │                                                     │  │  │
│  │  │ "Detected user intent: pricing"                     │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │ PART 4: Language Instruction (if not English)        │  │  │
│  │  │                                                     │  │  │
│  │  │ "IMPORTANT: Respond in 'te' (Telugu)"               │  │  │
│  │  ├─────────────────────────────────────────────────────┤  │  │
│  │  │ PART 5: Conversation History (last 6 messages)      │  │  │
│  │  │                                                     │  │  │
│  │  │ user: "hello"                                       │  │  │
│  │  │ assistant: "Welcome to Tickets99!"                  │  │  │
│  │  │ user: "how much does it cost?"  ← current message   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  Sends this to Ollama via HTTP POST:                      │  │
│  │    URL: http://localhost:11434/api/chat                    │  │
│  │    Model: phi3:mini (3.8B parameters)                     │  │
│  │    Temperature: 0.3 (low = more focused/factual)          │  │
│  │    Max tokens: 256                                        │  │
│  │    Timeout: 90 seconds                                    │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────┐                      │  │
│  │  │  Ollama SUCCEEDS?               │                      │  │
│  │  │  YES → Return LLM response      │──── HAPPY PATH ───▶ │  │
│  │  │  NO  → Go to FALLBACK ▼         │                      │  │
│  │  └─────────────────────────────────┘                      │  │
│  │                                                           │  │
│  │  FALLBACK (if Ollama times out or is offline):            │  │
│  │  1. Check intent → return pre-written response            │  │
│  │     "pricing" → "Free to list, 2-5% commission..."        │  │
│  │  2. No intent? → Return best ChromaDB FAQ match           │  │
│  │  3. No FAQ match? → Generic "I can help with..." message  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: RESPONSE PROCESSING  (main.py → _handle_chat)         │
│                                                                 │
│  • Checks for lead form trigger: [SHOW_LEAD_FORM:organizer]     │
│    If found → strips tag, sets showForm = "organizer"           │
│  • Saves assistant message to session history                   │
│  • Returns JSON response to frontend:                           │
│    {                                                            │
│      "success": true,                                           │
│      "message": "Tickets99 pricing is simple: free to list...", │
│      "sessionId": "ticket99_1234567890",                        │
│      "showForm": null,                                          │
│      "brand": "ticket99"                                        │
│    }                                                            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: FRONTEND DISPLAY  (widget JS)                          │
│                                                                 │
│  • Hides typing indicator                                       │
│  • Displays bot message in chat bubble                          │
│  • If showForm = "organizer" → shows lead capture form          │
│  • If showForm = "partner" → shows partnership inquiry form     │
│  • Stores sessionId for next message (conversation continuity)  │
└─────────────────────────────────────────────────────────────────┘
```


## Startup Flow (What Happens When Server Starts)

```
 python main.py
 │
 ▼
┌─────────────────────────────────────────────────────────────────┐
│  SERVER STARTUP  (main.py → lifespan)                           │
│                                                                 │
│  1. INITIALIZE VECTOR STORE (vector_store.py)                   │
│     │                                                           │
│     ├─► Load sentence-transformers model (all-MiniLM-L6-v2)    │
│     │   • Downloads ~80MB model on first run                    │
│     │   • Converts text → 384-dimensional vectors               │
│     │                                                           │
│     ├─► Read ticket99_faqs.json (45 Q&A pairs)                  │
│     │   • Combine each Q+A into a single text chunk             │
│     │   • Convert all 45 chunks → vector embeddings             │
│     │   • Store in ChromaDB collection "ticket99_knowledge"     │
│     │                                                           │
│     ├─► Read eventitans_faqs.json (35 Q&A pairs)                │
│     │   • Same process → "eventitans_knowledge" collection      │
│     │                                                           │
│     └─► Also loads any .txt files from docs/ directories        │
│                                                                 │
│  2. CHECK OLLAMA CONNECTION                                     │
│     • GET http://localhost:11434/api/tags                        │
│     • If OK → "Ollama connected (phi3:mini)"                    │
│     • If fails → "Ollama not available - fallback mode"         │
│                                                                 │
│  3. START UVICORN on http://localhost:8000                       │
│     • Single worker (avoids ChromaDB file locking on Windows)   │
│     • Mounts /widgets/ static files for frontend                │
│     • Registers all API endpoints                               │
└─────────────────────────────────────────────────────────────────┘
```


## Key Components Explained

### 1. Intent Classifier (`intent_classifier.py`)
**What:** Keyword-based pattern matching to detect what the user wants.
**Why:** Fast (< 1ms), reliable, no AI needed. Ensures "refund" always maps to refund info, "pricing" always maps to pricing, etc.
**How:** Uses word-boundary regex (`\brate\b`) for single words to prevent false matches (e.g., "rate" won't match inside "integrate"). Multi-word phrases use simple substring matching.

### 2. Vector Store / ChromaDB (`vector_store.py`)
**What:** A database that stores FAQ text as mathematical vectors (arrays of 384 numbers).
**Why:** Finds questions with SIMILAR MEANING, not just matching words. "how much does it cost?" finds "What is the pricing?" even though they share no words.
**How:** The `all-MiniLM-L6-v2` model converts text into vectors. ChromaDB compares vectors using cosine similarity. Closer vectors = more similar meaning.

### 3. RAG Chain (`rag_chain.py`)
**What:** The core pipeline that assembles everything and generates a response.
**Why:** Combines keyword matching (fast, reliable) with semantic search (smart) and LLM generation (natural language).
**How:**
1. Detect language → so the bot can respond in Hindi, Telugu, etc.
2. Classify intent → know what the user wants
3. Search ChromaDB → find relevant FAQ content
4. Build prompt → system prompt + FAQ context + intent hint + conversation history
5. Call Ollama → phi3:mini generates a natural response using all the context
6. Fallback → if Ollama is down, use intent-based pre-written responses

### 4. Conversation Manager (`conversation_manager.py`)
**What:** In-memory storage of chat sessions.
**Why:** So the bot remembers what you said earlier in the conversation. "Tell me more" makes sense because it knows the previous topic.
**How:** Dictionary keyed by sessionId. Stores last 6 messages. Sessions expire after 30 minutes.

### 5. Frontend Widgets (`ticket99-widget.js`, `eventitans-widget.js`)
**What:** Self-contained JavaScript chat widgets that can be embedded on any website.
**Why:** Drop a single `<script>` tag on any page and the chatbot appears.
**How:** IIFE (Immediately Invoked Function Expression) pattern. Injects all CSS inline. Uses DOM prefixes (`t99-`, `et-`) to avoid conflicts. Both can run on the same page simultaneously.


## Example: Full Trace of "I want a refund"

```
1. Widget sends: POST /api/ticket99/chat
   Body: { message: "I want a refund", sessionId: "ticket99_abc" }

2. main.py: _handle_chat("ticket99", request)
   → Saves "I want a refund" to session history
   → Calls generate_response("ticket99", "I want a refund", "ticket99_abc")

3. rag_chain.py: generate_response()
   → 3A: detect_language("I want a refund") → "en"
   → 3B: classify_intent("I want a refund") → ("refund", 0.94)
         ↳ "refund" keyword matched via \brefund\b
   → 3C: vector_search("ticket99", "I want a refund", top_k=3)
         ↳ Returns: [
             { question: "Can I get a refund?", answer: "Refund policies are set by...", distance: 0.38 },
             { question: "How do I cancel a ticket?", answer: "To cancel a ticket...", distance: 0.72 },
             { question: "What happens if event cancelled?", answer: "If cancelled...", distance: 0.89 }
           ]
   → 3D: Build prompt with system prompt + 3 FAQ chunks + "intent: refund" + history
         Send to Ollama phi3:mini
         ↳ SUCCESS: "Refund policies are determined by each event organizer.
            Please check the event page for specific terms, or reach out to
            us at support@tickets99.com with your booking ID! 😊"
         ↳ IF TIMEOUT: fallback → intent "refund" → "Refund policies are set
            by each event organizer. Check the event page for details, or
            email support@tickets99.com with your booking ID."

4. main.py: Check for [SHOW_LEAD_FORM:...] tag → none found
   → Save assistant message to session history
   → Return JSON response

5. Widget: Hide typing indicator, display bot message in chat bubble
```


## Two Response Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   MODE 1: LLM MODE (Ollama running)                             │
│   ─────────────────────────────────                             │
│   • Natural, conversational responses                           │
│   • Can understand context and nuance                           │
│   • Responds in user's language (Hindi, Telugu, etc.)           │
│   • Uses FAQ context to stay accurate                           │
│   • Takes 1-30 seconds depending on prompt size                 │
│                                                                 │
│   MODE 2: FALLBACK MODE (Ollama down or timeout)                │
│   ──────────────────────────────────────────────                │
│   • Uses intent classifier → pre-written responses              │
│   • If no intent match → returns best ChromaDB FAQ match        │
│   • Instant responses (< 100ms)                                 │
│   • Always accurate (responses are hand-written)                │
│   • Cannot handle nuance or language switching                  │
│   • 20 intent categories cover most common questions            │
│                                                                 │
│   The bot ALWAYS responds - it never returns an error to the    │
│   user. If everything fails, it returns a generic helpful       │
│   message directing them to the website or support email.       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```
