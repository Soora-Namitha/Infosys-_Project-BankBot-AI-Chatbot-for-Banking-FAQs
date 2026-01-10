from dialogue_manager.dialogue_handler import DialogueManager

dm = DialogueManager()

# simulate: no special intent, so it should go to LLM block
reply = dm.handle(intent=None, entities=None, user_text="What is a savings account?")
print("Bot:", reply)
