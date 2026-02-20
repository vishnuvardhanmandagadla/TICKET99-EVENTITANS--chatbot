import os
import re
import time
import json
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config import settings, BRAND_CONFIGS
from rag_chain import generate_response, check_ollama_health
from conversation_manager import (
    add_message,
    get_or_create_session,
    get_message_count,
    clear_session,
    cleanup_expired,
)
import vector_store
from whatsapp_handler import verify_webhook, handle_message

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    print("\n" + "=" * 55)
    print("  Dual-Brand AI Chatbot Server")
    print("  Tickets99 + Eventitans | RAG-powered")
    print("=" * 55)

    # Initialize vector store
    print("\n  Initializing knowledge base...")
    vector_store.initialize()

    # Check Ollama
    ollama_ok = await check_ollama_health()
    if ollama_ok:
        print(f"  [OK] Ollama connected ({settings.ollama_model})")
    else:
        print(f"  [WARN] Ollama not available - using FAQ fallback mode")

    print(f"\n  Server starting on http://localhost:{settings.app_port}")
    print(f"  Demo page: http://localhost:{settings.app_port}/demo")
    print("=" * 55 + "\n")

    yield

    # Shutdown
    print("\n  Server shutting down...")


app = FastAPI(title="Dual-Brand AI Chatbot", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Chat endpoints ---

async def _handle_chat(brand: str, request: Request) -> JSONResponse:
    """Shared chat handler for both brands."""
    try:
        data = await request.json()
        message = data.get("message", "").strip()
        session_id = data.get("sessionId")

        if not message:
            return JSONResponse({"error": "Message is required"}, status_code=400)

        conversation_id = session_id or f"{brand}_{int(time.time() * 1000)}"

        # Ensure session exists
        get_or_create_session(conversation_id)

        # Add user message
        add_message(conversation_id, "user", message)

        # Generate response
        assistant_message = await generate_response(brand, message, conversation_id)

        # Check for lead form trigger
        show_form = None
        clean_message = assistant_message

        form_match = re.search(r"\[SHOW_LEAD_FORM:(\w+)\]", assistant_message)
        if form_match:
            show_form = form_match.group(1)
            clean_message = re.sub(r"\s*\[SHOW_LEAD_FORM:\w+\]", "", assistant_message).strip()

        # Add assistant message to history
        add_message(conversation_id, "assistant", clean_message)

        return JSONResponse({
            "success": True,
            "message": clean_message,
            "sessionId": conversation_id,
            "showForm": show_form,
            "brand": brand,
        })

    except Exception as e:
        print(f"  [ERROR] Chat error ({brand}): {e}")
        return JSONResponse(
            {"error": "Failed to process message", "details": str(e)},
            status_code=500,
        )


@app.post("/api/ticket99/chat")
async def ticket99_chat(request: Request):
    return await _handle_chat("ticket99", request)


@app.post("/api/eventitans/chat")
async def eventitans_chat(request: Request):
    return await _handle_chat("eventitans", request)


# --- Leads endpoint ---

@app.post("/api/leads")
async def capture_lead(request: Request):
    try:
        lead_data = await request.json()
        lead_data["timestamp"] = datetime.now().isoformat()
        lead_data["source"] = "chatbot"

        print(f"  [LEAD] {json.dumps(lead_data, indent=2)}")

        return JSONResponse({"success": True, "message": "Lead captured successfully"})
    except Exception as e:
        print(f"  [ERROR] Lead error: {e}")
        return JSONResponse({"error": "Failed to submit lead"}, status_code=500)


# --- WhatsApp endpoints ---

@app.get("/api/whatsapp/webhook")
async def whatsapp_verify(request: Request):
    return await verify_webhook(request)


@app.post("/api/whatsapp/webhook")
async def whatsapp_incoming(request: Request):
    result = await handle_message(request)
    return JSONResponse(result)


# --- Health check ---

@app.get("/health")
async def health():
    ollama_ok = await check_ollama_health()

    # Cleanup expired sessions periodically
    cleaned = cleanup_expired()
    if cleaned:
        print(f"  [CLEANUP] Removed {cleaned} expired sessions")

    return JSONResponse({
        "status": "ok",
        "ollama": "connected" if ollama_ok else "unavailable",
        "model": settings.ollama_model,
        "brands": list(BRAND_CONFIGS.keys()),
        "timestamp": datetime.now().isoformat(),
    })


# --- Clear session ---

@app.post("/api/clear")
async def clear(request: Request):
    data = await request.json()
    session_id = data.get("sessionId")
    if session_id:
        clear_session(session_id)
    return JSONResponse({"success": True})


# --- Static files & demo ---

@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    demo_path = FRONTEND_DIR / "widgets" / "widget-demo.html"
    if demo_path.exists():
        return HTMLResponse(demo_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Demo page not found</h1><p>Ensure frontend/widgets/widget-demo.html exists.</p>")


# Mount static files for widgets
if FRONTEND_DIR.exists():
    app.mount("/widgets", StaticFiles(directory=str(FRONTEND_DIR / "widgets")), name="widgets")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.app_port,
        workers=1,  # Single worker to avoid ChromaDB file locking on Windows
        reload=False,
    )
