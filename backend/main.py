import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3-flash-preview"
SYSTEM = ("You are a financial planning assistant for users in India. Use rupees (₹) "
          "and Indian options like EPF, PPF, FD, mutual fund SIPs and NPS unless the user "
          "says otherwise. Help with budgeting, saving, investing basics and goal planning. "
          "Give clear, practical steps and keep answers short. You are not a licensed advisor.")

app = FastAPI()
import sqlite3
db = sqlite3.connect("chat.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, reply TEXT, time TEXT DEFAULT CURRENT_TIMESTAMP)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/chat")
def chat(data: dict):
    contents = [types.Content(role=h["role"], parts=[types.Part(text=h["text"])])
                for h in data.get("history", [])]
    contents.append(types.Content(role="user", parts=[types.Part(text=data["message"])]))
    try:
        res = client.models.generate_content(
            model=MODEL, contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM))
        db.execute("INSERT INTO chats (message, reply) VALUES (?, ?)", (data["message"], res.text))
        db.commit()
        return {"reply": res.text}
    except Exception as e:
        return {"reply": f"Error: {e}"}

@app.get("/history")
def get_history():
    rows = db.execute("SELECT message, reply, time FROM chats ORDER BY id DESC")
    return [dict(zip(("message", "reply", "time"), r)) for r in rows]