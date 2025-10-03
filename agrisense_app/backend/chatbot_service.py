from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    nlm_url = os.getenv("NLM_SERVICE_URL")
    if not nlm_url:
        raise HTTPException(status_code=500, detail="NLM service URL not configured")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{nlm_url}/chat",
                json={"message": request.message},
                timeout=10.0
            )
            response.raise_for_status()
            return ChatResponse(response=response.json().get("response", ""))
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"NLM service error: {str(e)}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"NLM service returned error: {e.response.text}")
