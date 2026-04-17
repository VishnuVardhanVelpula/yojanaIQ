import requests
import json

def test_vapi_webhook():
    url = "http://localhost:8000/api/vapi/webhook"
    
    # Mock Vapi payload for a 'tool-calls' message
    payload = {
        "message": {
            "type": "tool-calls",
            "toolCallList": [], # Legacy
            "toolCalls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "search_schemes",
                        "arguments": {
                            "query": "What schemes am I eligible for?",
                            "language": "English",
                            "profile": {
                                "age": 45,
                                "occupation": "farmer",
                                "income": 120000,
                                "gender": "male",
                                "caste": "OC"
                            }
                        }
                    }
                }
            ]
        }
    }
    
    print(f"Sending test payload to {url}...")
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print("Response JSON:")
        print(json.dumps(response.json(), indent=2))
        
        # Basic validation
        res_data = response.json()
        if "results" in res_data and len(res_data["results"]) > 0:
            result = res_data["results"][0]
            if result.get("toolCallId") == "call_123" and "result" in result:
                print("\nVerification SUCCESS: Webhook returned valid RAG response.")
            else:
                print("\nVerification FAILED: Unexpected response format.")
        else:
            print("\nVerification FAILED: No results returned.")
            
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure your FastAPI server is running on port 8000!")

if __name__ == "__main__":
    test_vapi_webhook()
