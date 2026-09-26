"""WebSocket live updates endpoint with authentication (Sections 51 & 53)."""

import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status

from src.fruitcraft_bot.core.events import ws_manager
from src.fruitcraft_bot.core.security import authenticate_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/dashboard")
async def dashboard_websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None)
):
    """
    Real-time updates WebSocket endpoint.
    Protected by token query parameter or first-message auth.
    Broadcasts worker_status, battle_started, battle_finished, gold_collected, quest_finished, error, captcha_required.
    """
    # Authenticate token
    user = authenticate_token(token)
    if not user:
        # Check Authorization header if present
        auth_header = websocket.headers.get("sec-websocket-protocol") or websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            user = authenticate_token(auth_header.split(" ")[1])

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(websocket)
    try:
        # Keep connection open and handle incoming ping/pong or messages
        while True:
            data = await websocket.receive_text()
            # Client can ping or send commands
            if data == "ping":
                await websocket.send_text('{"type": "pong"}')
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning("WebSocket connection closed with error: %s", e)
        await ws_manager.disconnect(websocket)
