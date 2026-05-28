import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import HumanMessage, AIMessage

from agent import astro_agent

load_dotenv()

app = FastAPI()

# ── Allow React frontend to talk to this server ─────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request model ────────────────────────────────────────────
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    birth_date: Optional[str] = ""
    birth_time: Optional[str] = ""
    birth_place: Optional[str] = ""

# ── Chat endpoint with streaming ─────────────────────────────
@app.post("/chat")
async def chat(request: ChatRequest):

    # Inject birth details into the last user message
    birth_context = ""
    if request.birth_date or request.birth_time or request.birth_place:
        birth_context = f"\n\n[User's birth details — use these automatically: Date: {request.birth_date}, Time: {request.birth_time}, Place: {request.birth_place}]"

    lc_messages = []
    for i, m in enumerate(request.messages):
        if m.role == "user":
            if i == len(request.messages) - 1 and birth_context:
                lc_messages.append(HumanMessage(content=m.content + birth_context))
            else:
                lc_messages.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            lc_messages.append(AIMessage(content=m.content))

    async def generate():
        try:
            result = astro_agent.invoke({
                "messages": lc_messages,
                "birth_date": request.birth_date or "",
                "birth_time": request.birth_time or "",
                "birth_place": request.birth_place or "",
                "chart_data": {}
            })

            final_message = result["messages"][-1]
            content = final_message.content

            # Stream word by word
            words = content.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == len(words) - 1 else word + " "
                yield f"data: {json.dumps({'text': chunk})}\n\n"

            # Check which tools were called
            tool_calls_made = []
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls_made.append(tc["name"])

            if tool_calls_made:
                yield f"data: {json.dumps({'tools_used': tool_calls_made})}\n\n"

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

# ── Health check ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "AstroAgent is running smoothly!"}