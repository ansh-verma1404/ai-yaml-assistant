from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv, dotenv_values
import os
import requests
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------
# LOAD ENV (STRONG FIX)
# ---------------------------
env_path = os.path.join(os.getcwd(), ".env")
print("Loading .env from:", env_path)

config = dotenv_values(env_path)
API_KEY = config.get("OPENROUTER_API_KEY")

print("Loaded API KEY:", API_KEY)

if not API_KEY:
    raise Exception("❌ OPENROUTER_API_KEY not found. Fix your .env file.")


# ---------------------------
# APP INIT
# ---------------------------
app = FastAPI()

# ---------------------------
# CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# REQUEST MODEL
# ---------------------------
class YAMLInput(BaseModel):
    yaml_text: str


# ---------------------------
# LLM FUNCTION
# ---------------------------
def analyze_yaml(yaml_text: str):
    prompt = f"""
You are an expert DevOps engineer.

Analyze the following Kubernetes YAML and respond in this format:

Explanation:
- Explain what this YAML does

Issues:
- List possible risks, misconfigurations, or improvements

Suggestions:
- Suggest improvements or best practices

YAML:
{yaml_text}
"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "AI YAML Assistant"
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
        )

        # Debug
        print("Status Code:", response.status_code)

        if response.status_code != 200:
            return f"LLM Error: {response.text}"

        data = response.json()

        if "choices" in data:
            return data["choices"][0]["message"]["content"]
        else:
            return f"Unexpected Response: {data}"

    except Exception as e:
        return f"Internal Error: {str(e)}"


# ---------------------------
# API
# ---------------------------
@app.post("/analyze")
def analyze(input: YAMLInput):
    if not input.yaml_text.strip():
        raise HTTPException(status_code=400, detail="YAML cannot be empty")

    result = analyze_yaml(input.yaml_text)

    return {
        "analysis": result
    }


# ---------------------------
# ROOT
# ---------------------------
@app.get("/")
def root():
    return {"message": "AI YAML Assistant is running 🚀"}
