# nlu_engine/infer_intent.py

"""  
Temporary rule-based IntentClassifier so the project runs without transformers.
"""

from typing import List, Dict, Any


class IntentClassifier:
    def __init__(self, model_dir: str = "models/intent_model"):
        # no transformer model loading
        pass

    def predict(self, text: str, topk: int = 1) -> List[Dict[str, Any]]:
        text_l = text.lower()
        scores = {
        "check_balance": 0.0,
        "transfer_money": 0.0,
        "card_block": 0.0,
        "find_atm": 0.0,
    }
        

        if "balance" in text_l:
            scores["check_balance"] = 1.0
            #intent = "check_balance"
        elif "transfer" in text_l or "send money" in text_l or "pay" in text_l:
            scores["transfer_money"] = 1.0
            intent = "transfer_money"
        elif "block" in text_l or "lost card" in text_l:
            scores["card_block"] = 1.0
            intent = "card_block"
        elif "atm" in text_l:
            scores["find_atm"] = 1.0
            intent = "find_atm"
        else:
             return []  # no intent -> fallback

        # return [{"intent": intent, "score": 1.0}]
        # Topk results
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:topk]
        return [{"intent": k, "score": v} for k, v in results]

if __name__ == "__main__":
    ic = IntentClassifier("models/intent_model")
    print(ic.predict("Please transfer 5000 from my savings account", topk=3))