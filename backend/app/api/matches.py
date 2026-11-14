"""HTTP and WebSocket interfaces to the same reactive matching engine."""
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import ValidationError
from app.core.matching import MatchRequest, match_sites

router = APIRouter()

@router.post('/matches/evaluate')
def evaluate_matches(req: MatchRequest):
    try:
        return match_sites(req)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.websocket('/ws/matches')
async def live_matches(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            message = await ws.receive_json()
            revision = message.get('revision') if isinstance(message, dict) else None
            try:
                if not isinstance(message, dict):
                    raise ValueError('Expected an object with parameters and revision')
                req = MatchRequest.model_validate(message.get('parameters', {}))
                result = await asyncio.to_thread(match_sites, req)
                await ws.send_json({'type': 'match_result', 'revision': revision, 'result': result})
            except (ValueError, ValidationError, HTTPException) as exc:
                await ws.send_json({'type': 'error', 'revision': revision, 'message': str(exc)})
    except WebSocketDisconnect:
        pass
