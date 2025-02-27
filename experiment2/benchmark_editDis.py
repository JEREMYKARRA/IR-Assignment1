import json
import time
import platform
import psutil
import sys
from itertools import product
import tracemalloc

def levenshtein_distance(str1, str2):
    M, N = len(str1), len(str2)
    D = [[0] * (N + 1) for _ in range(M + 1)]
    
    for i in range(M + 1):
        D[i][0] = i
    for j in range(N + 1):
        D[0][j] = j
    
    for i in range(1, M + 1):
        for j in range(1, N + 1):
            if str1[i-1] == str2[j-1]:
                substitution_cost = 0
            else:
                substitution_cost = 2
                
            D[i][j] = min(
                D[i-1][j] + 1,          
                D[i][j-1] + 1,          
                D[i-1][j-1] + substitution_cost  
            )
    
    return D[M][N]

def load_dictionary(file_path):
    dictionary = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                words = line.strip().lower().split()
                dictionary.update(words)
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
    return dictionary

def spell_check(word, dictionary, k=2):
    word = word.lower()
    if word in dictionary:
        return word
    
    candidates = []
    for dict_word in dictionary:
        distance = levenshtein_distance(word, dict_word)
        if distance <= k:
            candidates.append((dict_word, distance))
    
    if not candidates:
        return word  # Return original if no match found
    
    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]  # Return best match

def spell_check_phrase(phrase, dictionary, k=2):
    words = phrase.strip().split()
    corrected_words = [spell_check(word, dictionary, k) for word in words]
    return ' '.join(corrected_words)

def load_documents(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
        return []
    except json.JSONDecodeError:
        print("Error: Could not decode JSON file.")
        return []

def search_corrected_phrase(corrected_phrase, documents):

    matching_docs = []
    for doc in documents:
        for key in ["Title", "Author", "Bibliographic Source", "Abstract"]:
            if key in doc and corrected_phrase.lower() in doc[key].lower():
                matching_docs.append(doc)
                break 
    return matching_docs

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

def benchmark_spell_check(queries, dictionary, k=2):
    total_time = 0
    results = []
    
    tracemalloc.start()
    
    for query_item in queries:
        query = query_item["query"]
        expected = query_item["corrected"]
        
        # Time the spell check
        start_time = time.time()
        corrected = spell_check_phrase(query, dictionary, k)
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

def print_benchmark_results(results, system_info):
    """
    Print benchmark results in a formatted way.
    """
    print("\n========== SPELL CHECKER BENCHMARK RESULTS ==========")
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

if __name__ == "__main__":
    system_info = get_system_info()
    
    print("Loading dictionary...")
    dictionary = load_dictionary("dictionary.txt")
    print(f"Dictionary loaded with {len(dictionary)} words.")
    
    print("Loading test queries...")
    queries = load_test_queries("Assignment-data/spell_queries.json")
    print(f"Loaded {len(queries)} test queries.")
    
    # Benchmark
    print("Running benchmark...")
    benchmark_results = benchmark_spell_check(queries, dictionary, k=2)
    
    # Print results
    print_benchmark_results(benchmark_results, system_info)
    
    with open("experiment2/editDistanceResults.txt","w+") as file_out:
        file_out.write(f"- Total Queries: {benchmark_results['total_queries']}\n- Total Time: {benchmark_results['total_time']:.4f} seconds\n- Average Time per Query: {benchmark_results['average_time']:.4f} seconds\n- Correct Results: {benchmark_results['correct_count']}/{benchmark_results['total_queries']} ({benchmark_results['accuracy'] * 100:.2f}%)")