import json
import time
import platform
import psutil
import tracemalloc
from collections import defaultdict
from difflib import SequenceMatcher

class SpellChecker:
    def __init__(self, n=2):
        self.dictionary = set()
        self.documents = []
        self.n = n
        self.word_ngrams = defaultdict(set)

    def load_dictionary(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.dictionary = set(word.strip().lower() for word in f)
            self._preprocess_dictionary()
            return len(self.dictionary)
        except FileNotFoundError:
            print(f"Error: Dictionary file {file_path} not found.")
            return 0

    def load_documents(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.documents = json.load(f)
            return len(self.documents)
        except FileNotFoundError:
            print(f"Error: Document file {file_path} not found.")
            return 0
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {file_path}")
            return 0

    def _preprocess_dictionary(self):
        for word in self.dictionary:
            ngrams = self._generate_ngrams(word)
            for ngram in ngrams:
                self.word_ngrams[ngram].add(word)

    def _generate_ngrams(self, word):
        return set(word[i:i+self.n] for i in range(max(0, len(word)-self.n+1)))

    def _jaccard_similarity(self, set1, set2):
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0

    def _levenshtein_similarity(self, word1, word2):
        return SequenceMatcher(None, word1, word2).ratio()

    def correct_word(self, word, debug=False):
        if debug:
            print(f"Correcting word: {word}")
        candidates = []

        for candidate in self.dictionary:

            jaccard = self._jaccard_similarity(
                self._generate_ngrams(word.lower()), 
                self._generate_ngrams(candidate)
            )
            levenshtein = self._levenshtein_similarity(word.lower(), candidate)
            combined_score = 0.5 * jaccard + 0.5 * levenshtein

            candidates.append((candidate, combined_score))

        candidates = sorted(candidates, key=lambda x: x[1], reverse=True)

        candidates = [c for c in candidates if c[1] >= 0.5]

        if debug:
            print(f"Candidates for '{word}': {candidates[:5]}")  
        return candidates if candidates else [(word, 0.0)]

    def correct_phrase(self, phrase, debug=False):
        words = phrase.split()
        corrected_words = []
        all_corrections = {}

        for word in words:
            if word.lower() not in self.dictionary:
                corrections = self.correct_word(word, debug)
                corrected_words.append(corrections[0][0])  
                all_corrections[word] = corrections 
            else:
                corrected_words.append(word)
                all_corrections[word] = [(word, 1.0)] 

        return ' '.join(corrected_words), all_corrections

    def find_documents(self, phrase, debug=False):
        corrected_phrase, all_corrections = self.correct_phrase(phrase, debug)
        matching_docs = []

        for doc in self.documents:
            if corrected_phrase.lower() in doc.get('Title', '').lower() or corrected_phrase.lower() in doc.get('Abstract', '').lower():
                matching_docs.append(doc.get('Index', None))

        return corrected_phrase, all_corrections, matching_docs
    
    def spell_check_phrase(self, phrase):

        corrected_phrase, _ = self.correct_phrase(phrase)
        return corrected_phrase


def load_test_queries(file_path):

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
        return []
    except json.JSONDecodeError:
        print("Error: Could not decode JSON file.")
        return []


def format_bytes(bytes):

    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024 or unit == 'GB':
            return f"{bytes:.2f} {unit}"
        bytes /= 1024


def get_system_info():

    processor = platform.processor()
    if not processor:
        processor = platform.machine()
    
    memory = psutil.virtual_memory()
    total_memory = format_bytes(memory.total)
    
    return {
        "processor": processor,
        "total_memory": total_memory,
        "system": platform.system(),
        "python_version": platform.python_version()
    }


def benchmark_spell_checker(spell_checker, queries):

    total_time = 0
    results = []

    tracemalloc.start()
    
    for query_item in queries:
        query = query_item["query"]
        expected = query_item["corrected"]

        start_time = time.time()
        corrected = spell_checker.spell_check_phrase(query)
        end_time = time.time()
        
        query_time = end_time - start_time
        total_time += query_time
        
        results.append({
            "query": query,
            "corrected": corrected,
            "expected": expected,
            "correct": corrected == expected,
            "time": query_time
        })

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    avg_time = total_time / len(queries) if queries else 0
    correct_count = sum(1 for r in results if r["correct"])
    accuracy = correct_count / len(queries) if queries else 0
    
    benchmark_results = {
        "total_queries": len(queries),
        "total_time": total_time,
        "average_time": avg_time,
        "correct_count": correct_count,
        "accuracy": accuracy,
        "current_memory": format_bytes(current),
        "peak_memory": format_bytes(peak),
        "individual_results": results
    }
    
    return benchmark_results


def print_benchmark_results(results, system_info, algorithm_name):
    print(f"\n========== {algorithm_name} BENCHMARK RESULTS ==========")
    print(f"System Information:")
    print(f"  - Processor: {system_info['processor']}")
    print(f"  - Total Memory: {system_info['total_memory']}")
    print(f"  - Operating System: {system_info['system']}")
    print(f"  - Python Version: {system_info['python_version']}")
    
    print("\nBenchmark Summary:")
    print(f"  - Total Queries: {results['total_queries']}")
    print(f"  - Total Time: {results['total_time']:.4f} seconds")
    print(f"  - Average Time per Query: {results['average_time']:.4f} seconds")
    print(f"  - Correct Results: {results['correct_count']}/{results['total_queries']} ({results['accuracy'] * 100:.2f}%)")
    print(f"  - Peak Memory Usage: {results['peak_memory']}")
    
    print("\nIndividual Query Results:")
    for idx, result in enumerate(results['individual_results'], 1):
        print(f"  {idx}. Query: '{result['query']}'")
        print(f"     - Corrected: '{result['corrected']}'")
        print(f"     - Expected: '{result['expected']}'")
        print(f"     - Correct: {'✓' if result['correct'] else '✗'}")
        print(f"     - Time: {result['time']:.4f} seconds")


def measure_initialization_time(dictionary_path, docs_path=None):
    start_time = time.time()
 
    spell_checker = SpellChecker(n=2)
    init_time = time.time() - start_time

    dict_start_time = time.time()
    dict_count = spell_checker.load_dictionary(dictionary_path)
    dict_load_time = time.time() - dict_start_time

    docs_load_time = 0
    docs_count = 0
    if docs_path:
        docs_start_time = time.time()
        docs_count = spell_checker.load_documents(docs_path)
        docs_load_time = time.time() - docs_start_time
    
    total_time = time.time() - start_time
    
    return {
        "spell_checker": spell_checker,
        "initialization_time": init_time,
        "dictionary_load_time": dict_load_time,
        "documents_load_time": docs_load_time,
        "total_load_time": total_time,
        "dictionary_count": dict_count,
        "documents_count": docs_count
    }


def print_initialization_results(results):

    print(f"Initialization time: {results['initialization_time']:.4f} seconds")
    print(f"Dictionary load time: {results['dictionary_load_time']:.4f} seconds (Loaded {results['dictionary_count']} words)")
    
    if results['documents_load_time'] > 0:
        print(f"Documents load time: {results['documents_load_time']:.4f} seconds (Loaded {results['documents_count']} documents)")
    
    print(f"Total setup time: {results['total_load_time']:.4f} seconds")


if __name__ == "__main__":
    system_info = get_system_info()
    print("System Information:", system_info)

    dictionary_path = "dictionary.txt"
    documents_path = "Assignment-data/bool_docs.json"
    
    print("\nInitializing Hybrid Spell Checker and loading data...")
    init_results = measure_initialization_time(dictionary_path, documents_path)
    spell_checker = init_results["spell_checker"]
    print_initialization_results(init_results)
    
    print("\nLoading test queries...")
    queries_path = "Assignment-data/spell_queries.json"
    queries = load_test_queries(queries_path)
    print(f"Loaded {len(queries)} test queries.")
    
    print("\nRunning benchmark...")
    benchmark_results = benchmark_spell_checker(spell_checker, queries)
    

    print_benchmark_results(benchmark_results, system_info, "HYBRID SPELL CHECKER")

    print("\nSample Corrections (with detailed candidates):")
    sample_queries = ["akoustic", "abzorption", "bureacratic", "aproximatley"]
    for query in sample_queries:
        corrected, corrections = spell_checker.correct_phrase(query, debug=True)
        print(f"\n  '{query}' -> '{corrected}'")
        if query in corrections:
            print(f"  Top candidates for '{query}':")
            for candidate, score in corrections[query][:3]:
                print(f"    - '{candidate}' (score: {score:.4f})")
                
    with  open("experiment2/hybridResults.txt","w+") as file_out:
        file_out.write(f"- Total Queries: {benchmark_results['total_queries']}\n- Total Time: {benchmark_results['total_time']:.4f} seconds\n- Average Time per Query: {benchmark_results['average_time']:.4f} seconds\n- Correct Results: {benchmark_results['correct_count']}/{benchmark_results['total_queries']} ({benchmark_results['accuracy'] * 100:.2f}%)")
