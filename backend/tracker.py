import io, json, os
from datetime import datetime
import numpy as np
import pandas as pd
from fastapi import APIRouter
from nlp import categorize, retrain

router = APIRouter()
query = None  # main.py fills this in
NEEDS = {"rent", "bills", "food", "transport"}

def init():
    query("CREATE TABLE IF NOT EXISTS expenses (id INT AUTO_INCREMENT PRIMARY KEY, description VARCHAR(200), amount DECIMAL(10,2), category VARCHAR(30), created TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    query("CREATE TABLE IF NOT EXISTS goals (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), target DECIMAL(12,2), saved DECIMAL(12,2) DEFAULT 0)")

@router.post("/expenses")
def add_expense(d: dict):
    cat, amt = categorize(d["description"]), float(d["amount"])
    old = np.array([float(r[0]) for r in query("SELECT amount FROM expenses WHERE category=%s", (cat,))])
    alert = (f"Unusual {cat} expense: ₹{amt:.0f} is far above your average of ₹{old.mean():.0f}"
             if len(old) >= 4 and amt > old.mean() + 2 * max(old.std(), 1) else None)
    query("INSERT INTO expenses (description, amount, category) VALUES (%s, %s, %s)", (d["description"], amt, cat))
    return {"category": cat, "alert": alert}

@router.get("/summary")
def summary(income: float = 0):
    df = pd.DataFrame(query("SELECT id, description, amount, category, created FROM expenses"),
                      columns=["id", "description", "amount", "category", "created"])
    if df.empty:
        return {"total": 0, "by_category": {}, "by_month": {}, "budget": None, "recent": []}
    df["amount"] = df.amount.astype(float)
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/processed_expenses.csv", index=False)
    total, needs = df.amount.sum(), df[df.category.isin(NEEDS)].amount.sum()
    return {
        "total": total,
        "by_category": df.groupby("category").amount.sum().round(0).to_dict(),
        "by_month": df.groupby(pd.to_datetime(df.created).dt.strftime("%Y-%m")).amount.sum().round(0).to_dict(),
        "budget": {"needs_spent": needs, "wants_spent": total - needs, "savings": income - total,
                   "plan": {"needs": income * .5, "wants": income * .3, "savings": income * .2}} if income else None,
        "recent": df.tail(5)[["id", "description", "amount", "category"]].to_dict("records"),
    }

@router.post("/goals")
def add_goal(d: dict):
    query("INSERT INTO goals (name, target) VALUES (%s, %s)", (d["name"], d["target"]))
    return {"ok": True}

@router.post("/goals/{gid}/add")
def fund_goal(gid: int, d: dict):
    query("UPDATE goals SET saved = saved + %s WHERE id = %s", (d["amount"], gid))
    return {"ok": True}

@router.get("/goals")
def goals():
    return [dict(zip(("id", "name", "target", "saved"), r)) for r in query("SELECT id, name, target, saved FROM goals")]
@router.post("/expenses/{eid}/category")
def fix_category(eid: int, d: dict):
    query("UPDATE expenses SET category=%s WHERE id=%s", (d["category"], eid))
    return {"ok": True}

@router.post("/retrain")
def retrain_model():
    return retrain(query("SELECT description, category FROM expenses"))

@router.post("/import")
def import_csv(d: dict):
    df = pd.read_csv(io.StringIO(d["csv"])).dropna(subset=["description", "amount"])
    for desc, amt in zip(df.description, df.amount):
        query("INSERT INTO expenses (description, amount, category) VALUES (%s, %s, %s)", (desc, float(amt), categorize(str(desc))))
    return {"imported": len(df)}

@router.post("/backup")
def backup():
    folder = os.getenv("BACKUP_DIR", "backups")
    os.makedirs(folder, exist_ok=True)
    data = {t: [list(map(str, r)) for r in query(f"SELECT * FROM {t}")] for t in ("chats", "expenses", "goals")}
    path = os.path.join(folder, f"backup_{datetime.now():%Y%m%d_%H%M%S}.json")
    json.dump(data, open(path, "w"))
    return {"saved": path}