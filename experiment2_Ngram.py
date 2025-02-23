import json
import re
from collections import defaultdict

class NgramSpellChecker:
    def __init__(self, n=2):
        self.n = n
        self.dictionary = set()
        self.word_ngrams = {}
        self.ngram_words = defaultdict(set)
        self.word_to_docs = defaultdict(set)
        self.doc_contents = {}

    def load_dictionary(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    word = line.strip().lower()
                    if len(word) > 2:
                        self.dictionary.add(word)
                        word_ngrams = self.generate_ngrams(word)
                        self.word_ngrams[word] = word_ngrams
                        for ngram in word_ngrams:
                            self.ngram_words[ngram].add(word)
        except FileNotFoundError:
            print(f"Error: Dictionary file {file_path} not found.")

    def load_documents(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for doc in data:
                    doc_id = doc.get("Index", len(self.doc_contents) + 1)
                    text = " ".join(str(value) for value in doc.values()).lower()
                    self.doc_contents[doc_id] = text
                    
                    words = re.findall(r'\w+', text)
                    for word in words:
                        if len(word) > 2:
                            self.dictionary.add(word)
                            word_ngrams = self.generate_ngrams(word)
                            self.word_ngrams[word] = word_ngrams
                            for ngram in word_ngrams:
                                self.ngram_words[ngram].add(word)
                            self.word_to_docs[word].add(doc_id)
        except FileNotFoundError:
            print(f"Error: Could not find file {file_path}")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {file_path}")

    def generate_ngrams(self, word):
        return {word[i:i+self.n] for i in range(len(word) - self.n + 1)}

    def jaccard_similarity(self, set1, set2):
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union != 0 else 0

    def suggest_correction_word(self, word):
        word_ngrams = self.generate_ngrams(word)
        max_similarity = 0
        best_matches = []

        for candidate in self.dictionary:
            similarity = self.jaccard_similarity(word_ngrams, self.word_ngrams.get(candidate, set()))
            if similarity > max_similarity:
                max_similarity = similarity
                best_matches = [candidate]
            elif similarity == max_similarity:
                best_matches.append(candidate)

        return best_matches if best_matches else [word] 

    def suggest_correction(self, phrase):
        words = re.findall(r'\w+', phrase.lower())
        corrected_words = []
        
        for word in words:
            best_matches = self.suggest_correction_word(word)
            corrected_words.append(best_matches[0]) 

        corrected_phrase = " ".join(corrected_words)
        
        matching_docs = [doc_id for doc_id, text in self.doc_contents.items() if corrected_phrase in text]

        return {"corrected_phrase": corrected_phrase, "documents": matching_docs}

if __name__ == "__main__":
    spell_checker = NgramSpellChecker(n=2)
    spell_checker.load_dictionary("dictionary2.txt")
    spell_checker.load_documents("Assignment-data/bool_docs.json")
    test_phrase = "akoustic"
    result = spell_checker.suggest_correction(test_phrase)
    print(f"Corrected Phrase: {result['corrected_phrase']}")
    print(f"Found in document indexes: {result['documents']}")
