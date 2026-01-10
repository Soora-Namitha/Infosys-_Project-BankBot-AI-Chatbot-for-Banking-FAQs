# nlu_engine/nlu_router.py

from nlu_engine.infer_intent import IntentClassifier
from nlu_engine.entity_extractor import extract as extract_entities

ic = IntentClassifier()   # shared intent classifier


def run_nlu(user_text: str):
    # intents
    intents = ic.predict(user_text, topk=4)
    intent = intents[0]["intent"] if intents else None

    # entities: dict from entity_extractor.extract
    ent_dict = extract_entities(user_text)   # {'amount': [...], ...}

    # convert dict -> list[dict] for DialogueManager
    entities = []
    for name, values in ent_dict.items():
        for v in values:
            entities.append({"entity": name.upper(), "value": v})

    return intent, entities
