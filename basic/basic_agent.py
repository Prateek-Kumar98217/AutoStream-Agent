"""This is the basic agent made during initail modeling phase."""

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import InMemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage, HumanMessage
from typing_extensions import TypedDict
from typing import Annotated
import operator
import os
from dotenv import load_dotenv
load_dotenv()   

# state object that the graph will use to store and manage data across different nodes
class MessageState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int  #Records the number of times the LLM has been called(just in case requext quota management is required later on)

# model used for graph operations
model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))

# intializing the vector store with intial details/information
loader = TextLoader("./knowledgebase.md")
raw_docs = loader.load()

text_spliter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=50)
splits = text_spliter.split_documents(raw_docs)
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001", api_key=os.getenv("GEMINI_API_KEY"))

vectorstore = InMemoryVectorStore.from_documents(documents=splits, embedding=embeddings)

# tool definations
# tool for mock lead cature as per given in requirements
@tool
def mock_lead_capture(name: str, email: str, plateform: str):   
    "API tool to send data of the user to backend."
    print(f"Lead captured successfully: {name}, {email}, {plateform}")
    return True

# tool for retriveing required context from kb when the llm is prompted for product details, pricing and company policies.
@tool
def retrieve_context(query: str):
    "Retrievs the AutoStream pricing, features and company policies"
    docs = vectorstore.similarity_search(query = query, k = 2)
    return "\n".join([doc.page_content for doc in docs])

#tool binding
tools = [mock_lead_capture, retrieve_context]
tools_by_name = {t.name: t for t in tools}
model_with_tools = model.bind_tools(tools)

# node function definations
# node resposibel for llm operations
def llm_call(state: dict):
    messages = [
        model_with_tools.invoke(
            [SystemMessage(
                content = "You are a Converstaional Asssitant, tasked with helping the user navigate and understand the uses of AutoStream SaaS application. AutoStream is a automated video editing tool for content creators."
            )] + state["messages"]
        )
    ]
    return {
        "messages": messages,
        "llm_calls": state.get("llm_calls", 0) + 1
    }

# node resposible for tool operations
def tool_node(state: dict):
    "Performs the tool call"
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        tool_result = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content = str(tool_result), tool_call_id = tool_call["id"]))
    return {"messages": result}

#conditonal node for deciding the flow of graph 
def should_continue(state: dict):
    if state["messages"][-1].tool_calls:
        return "tool_node"
    else:
        return END

# constructing agent
agent_builder = StateGraph(MessageState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

# checkpointing for state management
checkpointer = InMemorySaver()
agent = agent_builder.compile(checkpointer = checkpointer)

config = {"configurable": {"thread_id": "agent_test_1"}}

# test loop for checking agent operations
while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Ending conversation.")
        break
    state_update = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]}, 
        config=config
    )
    ai_response = state_update["messages"][-1].content
    print(f"\nAgent: {ai_response}")
