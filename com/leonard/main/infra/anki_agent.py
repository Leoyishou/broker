import requests
import json

class AnkiAgent:
    def __init__(self, host='localhost', port=8765):
        self.base_url = f'http://{host}:{port}'

    def _invoke(self, action, **params):
        payload = {
            'action': action,
            'version': 6,
            'params': params
        }
        response = requests.post(self.base_url, json=payload)
        if response.ok:
            return response.json()
        else:
            response.raise_for_status()

    def add_note(self, deck_name, model_name, fields, tags=None):
        note = {
            'deckName': deck_name,
            'modelName': model_name,
            'fields': fields,
            'options': {
                'allowDuplicate': False,
                'duplicateScope': 'deck'
            },
            'tags': tags or []
        }
        return self._invoke('addNote', note=note)

    def create_deck(self, deck_name):
        return self._invoke('createDeck', deck=deck_name)

    def get_deck_names(self):
        return self._invoke('deckNames')

    def get_model_names(self):
        return self._invoke('modelNames')

    def get_model_field_names(self, model_name):
        return self._invoke('modelFieldNames', modelName=model_name)

    def sync(self):
        return self._invoke('sync')

# Example usage:
if __name__ == "__main__":
    anki = AnkiAgent()
    
    # Create a new deck
    anki.create_deck("Python Vocabulary")
    
    # Add a new note (card)
    fields = {
        "word": "",
        "cognition": ""
    }
    result = anki.add_note("Python Vocabulary", "Basic", fields, tags=["programming", "computer science"])
    
    if result:
        print(f"Note added successfully. Note ID: {result}")
    else:
        print("Failed to add note.")
    
    # Sync changes
    anki.sync()