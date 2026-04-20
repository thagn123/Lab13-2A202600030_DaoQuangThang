import json
import os
import random
from dotenv import load_dotenv

load_dotenv()
os.environ["LANGFUSE_DEBUG"] = "true"

from fastapi.testclient import TestClient
from app.main import app
from langfuse.decorators import langfuse_context
from app import incidents

def run_tests():
    client = TestClient(app)
    queries_path = os.path.join("data", "sample_queries.jsonl")
    queries = []
    with open(queries_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                queries.append(json.loads(line.strip()))
                
    print("--- 1. Running NORMAL traffic (20 req) ---")
    for _ in range(20):
        q = random.choice(queries)
        client.post("/chat", json=q)
        
    print("--- 2. Running RAG SLOW incident (10 req - This will take 30 seconds to finish) ---")
    incidents.enable("rag_slow")
    for _ in range(10):
        q = random.choice(queries)
        client.post("/chat", json=q)
    incidents.disable("rag_slow")
    
    print("--- 3. Running COST SPIKE incident (10 req) ---")
    incidents.enable("cost_spike")
    for _ in range(10):
        q = random.choice(queries)
        client.post("/chat", json=q)
    incidents.disable("cost_spike")

    print("--- 4. Running ERROR incident (5 req) ---")
    incidents.enable("tool_fail")
    for _ in range(5):
        q = random.choice(queries)
        client.post("/chat", json=q)
    incidents.disable("tool_fail")
            
    # Force flush before exit
    try:
        langfuse_context.flush()
        print("Langfuse explicit flush completed. DONE!")
    except Exception as e:
        print(f"Langfuse flush error: {e}")

if __name__ == "__main__":
    run_tests()
