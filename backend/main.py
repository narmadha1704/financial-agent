from nlp import detect_intent
import os
import pymysql
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

def query(sql, args=()):
    db = pymysql.connect(host=os.getenv("DB_HOST", "localhost"), user=os.getenv("DB_USER", "root"),
                         password=os.getenv("DB_PASSWORD", ""), database=os.getenv("DB_NAME", "financial_agent"),
                         autocommit=True)
    with db, db.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchall()

query("CREATE TABLE IF NOT EXISTS chats (id INT AUTO_INCREMENT PRIMARY KEY, message TEXT, reply TEXT, time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
import tracker
tracker.query = query
tracker.init()
app.include_router(tracker.router)
@app.post("/chat")
def chat(data: dict):
    intent, conf = detect_intent(data["message"])
    contents = [types.Content(role=h["role"], parts=[types.Part(text=h["text"])])
                for h in data.get("history", [])]
    contents.append(types.Content(role="user", parts=[types.Part(text=data["message"])]))
    try:
        res = client.models.generate_content(
            model=MODEL, contents=contents,
            config=types.GenerateContentConfig(system_instruction=f"{SYSTEM} The user's question is about: {intent}."))
        query("INSERT INTO chats (message, reply) VALUES (%s, %s)", (data["message"], res.text))
        return {"reply": res.text, "intent": intent, "confidence": round(conf, 2)}
    except Exception as e:
        return {"reply": f"Error: {e}"}
@app.get("/insights")
def insights(income: float = 0):
    s = tracker.summary(income)
    try:
        res = client.models.generate_content(
            model=MODEL, config=types.GenerateContentConfig(system_instruction=SYSTEM),
            contents=f"Analyse my spending data. Give 4 short insights and 3 actions. Data: {s}")
        return {"insights": res.text}
    except Exception as e:
        return {"insights": f"Error: {e}"}