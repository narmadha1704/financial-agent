import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

examples = {
    "budgeting": ["how do i make a monthly budget", "split my salary into needs and wants", "track my expenses",
                  "explain the 50/30/20 rule", "reduce my monthly spending", "plan my household budget"],
    "saving": ["how much can i save each month", "build an emergency fund", "best way to save money",
               "saving goal for a bike", "how to save more from my salary", "recurring deposit or savings account"],
    "investing": ["should i invest in mutual funds", "what is a sip", "stocks vs fixed deposit",
                  "how to start investing", "best investment for beginners", "index fund returns"],
    "debt": ["how to pay off my loan", "credit card debt help", "should i prepay my education loan",
             "how to reduce my emi", "i owe money how to clear debt", "loan interest rate is too high"],
    "tax": ["how to save income tax", "what is section 80c", "old vs new tax regime",
            "tax on mutual fund gains", "how to file itr", "tax deductions for salaried"],
}
data = pd.DataFrame([(t, k) for k, v in examples.items() for t in v], columns=["text", "intent"])
vec = TfidfVectorizer(ngram_range=(1, 2))
model = LogisticRegression(max_iter=1000).fit(vec.fit_transform(data.text), data.intent)

def detect_intent(text):
    probs = model.predict_proba(vec.transform([text]))[0]
    i = int(np.argmax(probs))
    return model.classes_[i], float(probs[i])
cats = {
    "food": ["swiggy dinner", "zomato order", "groceries", "restaurant lunch", "tea and snacks", "vegetables market"],
    "rent": ["house rent", "room rent", "pg rent", "rent payment", "landlord", "hostel fees"],
    "transport": ["uber ride", "auto fare", "petrol", "bus ticket", "metro recharge", "train ticket"],
    "shopping": ["amazon order", "new shirt", "shoes", "myntra clothes", "phone cover", "gift purchase"],
    "bills": ["electricity bill", "mobile recharge", "wifi bill", "water bill", "gas cylinder", "dth recharge"],
    "entertainment": ["movie tickets", "netflix", "spotify", "gaming", "concert", "outing with friends"],
}
cdata = pd.DataFrame([(t, k) for k, v in cats.items() for t in v], columns=["text", "cat"])
cvec = TfidfVectorizer(ngram_range=(1, 2))
cmodel = LogisticRegression(max_iter=1000).fit(cvec.fit_transform(cdata.text), cdata.cat)

def categorize(text):
    return str(cmodel.predict(cvec.transform([text]))[0])
import json, os
import joblib
from sklearn.model_selection import cross_val_score

MODELS = os.path.join(os.path.dirname(__file__), "models")
if os.path.exists(f"{MODELS}/categorizer.joblib"):
    cvec, cmodel = joblib.load(f"{MODELS}/categorizer.joblib")

def retrain(extra):
    global cvec, cmodel
    df = pd.concat([cdata, pd.DataFrame(extra, columns=["text", "cat"])], ignore_index=True)
    cvec = TfidfVectorizer(ngram_range=(1, 2))
    X = cvec.fit_transform(df.text)
    cmodel = LogisticRegression(max_iter=1000).fit(X, df.cat)
    os.makedirs(MODELS, exist_ok=True)
    joblib.dump((cvec, cmodel), f"{MODELS}/categorizer.joblib")
    acc = float(np.mean(cross_val_score(LogisticRegression(max_iter=1000), X, df.cat, cv=3)))
    result = {"samples": len(df), "cv_accuracy": round(acc, 2)}
    json.dump(result, open(f"{MODELS}/results.json", "w"))
    return result