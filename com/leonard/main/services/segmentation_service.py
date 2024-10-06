import jieba
from typing import List
from infra.anki_agent import AnkiAgent

class SegmentationService:
    def __init__(self):
        self.anki_agent = AnkiAgent()

    @staticmethod
    def is_chinese(char):
        return '\u4e00' <= char <= '\u9fff'

    @staticmethod
    def process_word(word):
        word = word.lower()
        return ''.join(char for char in word if SegmentationService.is_chinese(char) or char.isalpha())

    @staticmethod
    def segment_and_deduplicate(text: str) -> List[str]:
        words = jieba.lcut(text)
        return list(set(words))

    def segment_and_add_to_anki(self, text: str, tag: str, deck_name: str, model_name: str) -> List[str]:
        words = self.segment_and_deduplicate(text)
        processed_words = []
        
        for word in words:
            processed_word = self.process_word(word)
            if processed_word:
                processed_words.append(processed_word)
                fields = {
                    "word": processed_word,
                    "cognition": ""
                }
                self.anki_agent.add_note(deck_name, model_name, fields, tags=[tag])
        
        return processed_words