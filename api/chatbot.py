import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hybrid_rag_system import HybridRAGSystem
import json

def handler(request):
    try:
        body = request.body.decode("utf-8")
        data = json.loads(body)
        query = data.get("query", "")
        if not query:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'query' in request body."})
            }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid request: {e}"})
        }

    rag = HybridRAGSystem()
    answer = rag.chat(query)
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"answer": answer})
    } 