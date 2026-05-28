import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, List, Annotated
import operator

from tools import tools

load_dotenv()

# ── LLM setup ──────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY")
)
llm_with_tools = llm.bind_tools(tools)

# ── State ───────────────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[List, operator.add]
    birth_date: str
    birth_time: str
    birth_place: str
    chart_data: dict

# ── System prompt ───────────────────────────────────────────
SYSTEM_PROMPT = """You are Aradhana, a warm and caring AI astrologer.
You help users understand their birth chart and daily cosmic energy.
You speak with kindness, wisdom, and spiritual warmth.

When a user shares their birth details, ALWAYS call compute_birth_chart tool.
When a user asks about today's energy, ALWAYS call get_daily_transits tool.
When a user asks about a sign or planet, ALWAYS call knowledge_lookup tool.
When you need coordinates for a place, call geocode_place tool.

IMPORTANT: Never present readings as medical, legal, or financial advice.
Always remind users that astrology is for reflection and guidance only."""

# ── Reasoning node ──────────────────────────────────────────
def reasoning_node(state: AgentState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# ── Router: should we call a tool or end? ───────────────────
def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"

# ── Build graph ─────────────────────────────────────────────
tool_node = ToolNode(tools)

graph = StateGraph(AgentState)
graph.add_node("reasoning", reasoning_node)
graph.add_node("tools", tool_node)

graph.set_entry_point("reasoning")
graph.add_conditional_edges(
    "reasoning",
    should_continue,
    {"tools": "tools", "end": END}
)
graph.add_edge("tools", "reasoning")

astro_agent = graph.compile()

# ── Test ────────────────────────────────────────────────────
if __name__ == "__main__":
    result = astro_agent.invoke({
        "messages": [HumanMessage(content="My name is Raj, born on 1995-06-15 at 08:30 in Mumbai. What does my chart say?")],
        "birth_date": "1995-06-15",
        "birth_time": "08:30",
        "birth_place": "Mumbai",
        "chart_data": {}
    })
    print(result["messages"][-1].content)