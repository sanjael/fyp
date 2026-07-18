import asyncio
from app.core.clients.ollama_client import OllamaHTTPClient
from app.core.clients.langchain_adapter import OllamaChatAdapter
from langchain_core.messages import HumanMessage

async def verify_ollama():
    print("1. Testing Raw HTTP Client...")
    try:
        client = OllamaHTTPClient(base_url="http://localhost:11434")
        res = client.generate(model="qwen2.5:latest", prompt="What is 2+2? Reply with just the number.")
        print(f"Raw HTTP Response: {res}")
        if "4" in res:
            print("Raw HTTP Client PASS")
        else:
            print("Raw HTTP Client FAIL - Unexpected output")
    except Exception as e:
        print(f"Raw HTTP Client FAIL: {e}")

    print("\n2. Testing LangChain Adapter...")
    try:
        adapter = OllamaChatAdapter(model_name="qwen2.5:latest", base_url="http://localhost:11434")
        message = HumanMessage(content="What is 5+5? Reply with just the number.")
        # Test sync
        res_sync = adapter.invoke([message])
        print(f"Adapter Sync Response: {res_sync.content}")
        
        # Test async
        res_async = await adapter.ainvoke([message])
        print(f"Adapter Async Response: {res_async.content}")
        
        if "10" in res_sync.content and "10" in res_async.content:
            print("LangChain Adapter PASS")
        else:
            print("LangChain Adapter FAIL - Unexpected output")
            
    except Exception as e:
        print(f"LangChain Adapter FAIL: {e}")

if __name__ == "__main__":
    asyncio.run(verify_ollama())
