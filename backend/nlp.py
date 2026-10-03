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