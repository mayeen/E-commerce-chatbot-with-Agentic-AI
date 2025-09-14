from typing import Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from .prompts import SYSTEM_PROMPT, CLASSIFY_PROMPT
from .tools import product_search, order_lookup
from ..config import settings

class State(BaseModel):
    messages: list = []  
    intent: Literal["product","order","smalltalk", "unknown"] | None = None
    last_tool_result: dict | None = None

# ---- LLM ----

llm = ChatGoogleGenerativeAI(
    model=settings.gemini_model,
    google_api_key=settings.google_api_key,
    temperature=0.2,
)

# ---- Nodes ----

def start(state: State) -> State:
    msgs = state.messages or []
    if not msgs or not isinstance(msgs[-1], HumanMessage):
        msgs.append(HumanMessage(content="Hello"))
    state.messages = [SystemMessage(content=SYSTEM_PROMPT)] + msgs
    return state


def classify_intent(state: State) -> State:
    human = [m for m in state.messages if isinstance(m, HumanMessage)][-1]
    prompt = ChatPromptTemplate.from_template(CLASSIFY_PROMPT)
    label = llm.invoke(prompt.format(text=human.content)).content.strip().lower()
    if label not in {"product","order","smalltalk"}:
        label = "unknown"
    state.intent = label  # type: ignore
    return state


def maybe_tool(state: State) -> State:
    human = [m for m in state.messages if isinstance(m, HumanMessage)][-1]

    if state.intent == "product":
        result = product_search.invoke({"query": human.content})
        state.last_tool_result = result

    elif state.intent == "order":
        import re
        m = re.search(r"(\d+)", human.content)
        order_id = int(m.group(1)) if m else 1
        result = order_lookup.invoke({"order_id": order_id})
        state.last_tool_result = result

    else:
        pass

    return state


def respond(state: State) -> State:
    human = [m for m in state.messages if isinstance(m, HumanMessage)][-1]
    ctx = state.last_tool_result

    if ctx:
        summary = f"Here is what I found: {ctx}"
    else:
        summary = "Let me help with that. Can you share more details?"

    reply = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"User: {human.content}\nContext: {summary}\nReply in 2-3 sentences.")
    ])
    state.messages += [AIMessage(content=reply.content)]
    return state

# ---- Graph ----
workflow = StateGraph(State)
workflow.add_node("start", start)
workflow.add_node("classify", classify_intent)
workflow.add_node("maybe_tool", maybe_tool)
workflow.add_node("respond", respond)

workflow.set_entry_point("start")
workflow.add_edge("start", "classify")
workflow.add_edge("classify", "maybe_tool")
workflow.add_edge("maybe_tool", "respond")
workflow.add_edge("respond", END)

graph = workflow.compile()

# Public runner
def run_agent(user_text: str) -> dict:
    init = State(messages=[HumanMessage(content=user_text)])
    out = graph.invoke(init)
    messages = out["messages"] if isinstance(out, dict) else out.messages
    last_ai = [m for m in messages if isinstance(m, AIMessage)][-1]
    intent = out["intent"] if isinstance(out, dict) else out.intent
    tool_result = out.get("last_tool_result") if isinstance(out, dict) else out.last_tool_result
    return {
        "intent": intent,
        "tool_result": tool_result,
        "answer": last_ai.content,
    }