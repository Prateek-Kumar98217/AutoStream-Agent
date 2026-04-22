import operator
import requests
from typing_extensions import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langgraph.graph import START, END, StateGraph
from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from demo.core.rag import AgentVectorStore
from demo.core.prompt import SYSTEM_PROMPT
from demo.config import settings

vector_store = AgentVectorStore(settings.STORE_DIR, api_key=settings.GEMINI_API_KEY)
vector_store.ingest_directory("data/knowledge_base")

model = ChatGoogleGenerativeAI(model="gemma-4-31b-it", api_key=settings.GEMINI_API_KEY)

class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

@tool
def retrieve_context(query: str) -> str:
    """Retrieve data from the knowledge base"""
    return vector_store.search(query)

@tool
def capture_lead(name: str, email: str, platform: str):
    """API tool to send lead data to backend"""
    try:
        response = requests.post(settings.mock_backend_url, json={"name": name, "email": email, "platform": platform})
        return response.json()
    except requests.exceptions.RequestException as e:
        return f"Failed to connect to backend: {e}"

tools =[retrieve_context, capture_lead]
tools_by_name = {t.name: t for t in tools}
model_with_tools = model.bind_tools(tools)

def llm_node(state: MessageState) -> MessageState:
    messages = [
        model_with_tools.invoke(
            [SystemMessage(
                content=SYSTEM_PROMPT
            )] + state["messages"]
        )
    ]

    return {
        "messages": messages,
        "llm_calls": state.get("llm_calls", 0) + 1
    }

def tool_node(state: MessageState):
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        tool_result = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content = str(tool_result), tool_call_id = tool_call["id"]))
    return {"messages": result}

def should_continue(state: MessageState):
    if state["messages"][-1].tool_calls:
        return "tool_node"
    else:
        return END

agent_builder = StateGraph(MessageState)

agent_builder.add_node("llm_node", llm_node)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_node")
agent_builder.add_conditional_edges("llm_node", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_node")

checkpointer = InMemorySaver()
agent = agent_builder.compile(checkpointer = checkpointer)
