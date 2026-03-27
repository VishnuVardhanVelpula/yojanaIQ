import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from rule_filter import rule_filter
from rag import run_rag

app = FastAPI(title="YojanaIQ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserProfile(BaseModel):
    age: int
    gender: str
    caste: str
    religion: str
    occupation: str
    income: int
    flags: Optional[List[str]] = []
    language: Optional[str] = "English"

class ChatRequest(BaseModel):
    profile: UserProfile
    query: str
    language: Optional[str] = "English"

@app.post("/api/match")
def match_schemes(profile: UserProfile):
    try:
        prof_dict = profile.model_dump()
        if 'flags' not in prof_dict or prof_dict['flags'] is None:
            prof_dict['flags'] = []
            
        lang = prof_dict.get('language', 'English')
        matched, rejected = rule_filter(prof_dict)
        
        # Translate matched cards if language is not English
        if lang != "English" and len(matched) > 0:
            import os, json
            from groq import Groq
            client = Groq(api_key=os.environ["GROQ_API_KEY"])
            
            payload = [{"id": m["id"], "name": m["name"], "category": m["category"], "benefits": m["benefits"]} for m in matched]
            
            prompt = f"Translate the 'name', 'category', and 'benefits' values in this JSON strictly to {lang}. Keep 'id' exactly as is. Output format MUST be a valid JSON object with a single key 'translated' containing the array of translated objects.\n\nJSON: {json.dumps(payload)}"
            
            try:
                res = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{"role": "system", "content": prompt}],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                trans_data = json.loads(res.choices[0].message.content)
                trans_items = trans_data.get("translated", payload)
                
                # Merge translated fields back into matched array
                trans_map = {t["id"]: t for t in trans_items if "id" in t}
                for m in matched:
                    if m["id"] in trans_map:
                        m["name"] = trans_map[m["id"]].get("name", m["name"])
                        m["category"] = trans_map[m["id"]].get("category", m["category"])
                        m["benefits"] = trans_map[m["id"]].get("benefits", m["benefits"])
            except Exception as e:
                print(f"Translation failed, falling back to English: {e}")

        return {"matched": matched, "rejected": rejected}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat_with_rag(req: ChatRequest):
    try:
        prof_dict = req.profile.model_dump()
        if 'flags' not in prof_dict or prof_dict['flags'] is None:
            prof_dict['flags'] = []
            
        result = run_rag(prof_dict, user_query=req.query, language=req.language)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
