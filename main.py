from langchain_core.messages import HumanMessage
from demo.agent import agent
import threading
import uvicorn
import time

def run_api():
    uvicorn.run("demo.api:app", host="127.0.0.1", port=8000, log_level="info")

def main():
    print("Staring the Mock API Backend in background...")
    api_thread = threading.Thread(target=run_api, daemon=True)
    api_thread.start()

    time.sleep(1.5)

    config = {"configurable": {"thread_id": "test_session_01"}}

    print("AutoStream Conversation Agent is online.")
    print("Type 'quit' or 'exit' to exit")
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() == "quit" or user_input.lower() == "exit":
                print("Shutting down system...")
                break
            if not user_input.strip():
                continue
            state_update = agent.invoke(
                {"messages" : [HumanMessage(content=user_input)]},
                config=config
            )
            agent_response = state_update["messages"][-1].content
            if isinstance(agent_response, list):
                text_response = next((item['text'] for item in agent_response if item.get("type") == 'text'), "")
                print(f"\nAgent: {text_response}\n")
            else:
                print(f"\nAgent: {agent_response}\n")
        except KeyboardInterrupt:
            print("Shutting down system due to keyboard interruption...")
            break
    
if __name__ == "__main__":
    main()