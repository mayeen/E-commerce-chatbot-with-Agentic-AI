from dotenv import load_dotenv

from fastapi import FastAPI
from pydantic import BaseModel
from app.agents.support_agent import run_agent

 
app = FastAPI(title="Agentic MVP")
load_dotenv()
class ChatIn(BaseModel):
    message: str

class ChatOut(BaseModel):
    intent: str | None
    tool_result: dict | None
    answer: str

@app.get("/")
async def root():
    return {"ok": True, "service": "agentic-mvp"}

@app.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn):
    return run_agent(body.message)