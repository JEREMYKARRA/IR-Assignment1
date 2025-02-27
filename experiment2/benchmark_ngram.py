import json
import re
import time
import platform
import psutil
import tracemalloc
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
            return len(self.dictionary)
        except FileNotFoundError:
            print(f"Error: Dictionary file {file_path} not found.")
            return 0

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
            return len(data)
        except FileNotFoundError:
            print(f"Error: Could not find file {file_path}")
            return 0
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {file_path}")
            return 0

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
    
    def spell_check_phrase(self, phrase):
        result = self.suggest_correction(phrase)
        return result["corrected_phrase"]


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
    
    spell_checker = NgramSpellChecker(n=2)
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

    print("\n========== INITIALIZATION BENCHMARK ==========")
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

    print("\nInitializing N-gram Spell Checker and loading data...")
    init_results = measure_initialization_time(dictionary_path, documents_path)
    spell_checker = init_results["spell_checker"]
    print_initialization_results(init_results)

    print("\nLoading test queries...")
    queries_path = "Assignment-data/spell_queries.json"
    queries = load_test_queries(queries_path)
    print(f"Loaded {len(queries)} test queries.")
    print("\nRunning benchmark...")
    benchmark_results = benchmark_spell_checker(spell_checker, queries)

    print_benchmark_results(benchmark_results, system_info, "N-GRAM SPELL CHECKER")

    print("\nSample Corrections:")
    sample_queries = ["akoustic", "abzorption", "bureacratic", "aproximatley"]
    for query in sample_queries:
        corrected = spell_checker.spell_check_phrase(query)
        print(f"  '{query}' -> '{corrected}'")

    with  open("experiment2/nGramResults.txt","w+") as file_out:
        file_out.write(f"- Total Queries: {benchmark_results['total_queries']}\n- Total Time: {benchmark_results['total_time']:.4f} seconds\n- Average Time per Query: {benchmark_results['average_time']:.4f} seconds\n- Correct Results: {benchmark_results['correct_count']}/{benchmark_results['total_queries']} ({benchmark_results['accuracy'] * 100:.2f}%)")