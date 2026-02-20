"""Placeholder WhatsApp webhook handler for future integration."""

import json
from fastapi import Request, Response


async def verify_webhook(request: Request) -> Response:
    """Handle WhatsApp webhook verification (GET).
    WhatsApp sends a challenge token that must be echoed back.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    # TODO: Replace with actual verify token from WhatsApp Business API settings
    verify_token = "tickets99_whatsapp_verify"

    if mode == "subscribe" and token == verify_token:
        print(f"  [WhatsApp] Webhook verified")
        return Response(content=challenge, media_type="text/plain")

    return Response(content="Forbidden", status_code=403)


async def handle_message(request: Request) -> dict:
    """Handle incoming WhatsApp messages (POST).
    Logs the incoming data for now.
    """
    try:
        body = await request.json()
        print(f"  [WhatsApp] Incoming: {json.dumps(body, indent=2)}")

        # TODO: Extract message, determine brand, call generate_response,
        # and send reply via WhatsApp Business API

        return {"status": "received"}
    except Exception as e:
        print(f"  [WhatsApp] Error: {e}")
        return {"status": "error", "message": str(e)}
