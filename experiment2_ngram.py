import json
from collections import defaultdict
from difflib import SequenceMatcher

class SpellChecker:
    def __init__(self, n=2):
        self.dictionary = set()
        self.documents = []
        self.n = n
        self.word_ngrams = defaultdict(set)

    def load_dictionary(self, file_path):
        with open(file_path, 'r') as f:
            self.dictionary = set(word.strip().lower() for word in f)
        self._preprocess_dictionary()

    def load_documents(self, file_path):
        with open(file_path, 'r') as f:
            self.documents = json.load(f)  # Load JSON as a list of documents

    def _preprocess_dictionary(self):
        for word in self.dictionary:
            ngrams = self._generate_ngrams(word)
            for ngram in ngrams:
                self.word_ngrams[ngram].add(word)

    def _generate_ngrams(self, word):
        return set(word[i:i+self.n] for i in range(len(word)-self.n+1))

    def _jaccard_similarity(self, set1, set2):
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0

    def _levenshtein_similarity(self, word1, word2):
        return SequenceMatcher(None, word1, word2).ratio()

    def correct_word(self, word):
        print(f"Correcting word: {word}")
        candidates = []

        for candidate in self.dictionary:
            # Combine Jaccard and Levenshtein similarities
            jaccard = self._jaccard_similarity(
                self._generate_ngrams(word.lower()), 
                self._generate_ngrams(candidate)
            )
            levenshtein = self._levenshtein_similarity(word.lower(), candidate)
            combined_score = 0.5 * jaccard + 0.5 * levenshtein

            candidates.append((candidate, combined_score))

        # Sort candidates by similarity in descending order
        candidates = sorted(candidates, key=lambda x: x[1], reverse=True)

        # Filter out candidates with low similarity (e.g., < 0.5)
        candidates = [c for c in candidates if c[1] >= 0.5]

        print(f"Candidates for '{word}': {candidates}")
        return candidates if candidates else [(word, 0.0)]

    def correct_phrase(self, phrase):
        words = phrase.split()
        corrected_words = []
        all_corrections = {}

        for word in words:
            if word.lower() not in self.dictionary:
                corrections = self.correct_word(word)
                corrected_words.append(corrections[0][0])  # Take the top correction
                all_corrections[word] = corrections  # Store all corrections
            else:
                corrected_words.append(word)
                all_corrections[word] = [(word, 1.0)]  # Exact match

        return ' '.join(corrected_words), all_corrections

    def find_documents(self, phrase):
        corrected_phrase, all_corrections = self.correct_phrase(phrase)
        matching_docs = []

        # Iterate over the list of documents
        for doc in self.documents:
            # Check if the corrected phrase exists in Title or Abstract
            if corrected_phrase.lower() in doc['Title'].lower() or corrected_phrase.lower() in doc['Abstract'].lower():
                matching_docs.append(doc['Index'])

        return corrected_phrase, all_corrections, matching_docs


# Usage example
spell_checker = SpellChecker(n=2)  # Use bigrams (n=2) for better handling of short words
spell_checker.load_dictionary("dictionary2.txt")
spell_checker.load_documents("Assignment-data/bool_docs.json")

query = "acclartion"
corrected_phrase, all_corrections, matching_docs = spell_checker.find_documents(query)

print(f"Original query: {query}")
print(f"Corrected query: {corrected_phrase}")
print(f"Matching documents: {matching_docs}")
print("\nAll possible corrections:")
for word, corrections in all_corrections.items():
    print(f"{word}: {corrections}")