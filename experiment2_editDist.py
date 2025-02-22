import json
from itertools import product

def levenshtein_distance(str1, str2):
    """
    Calculate the Levenshtein distance between two strings using dynamic programming.
    """
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

def load_documents(file_path):
    """
    Load documents from a JSON file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
        return []
    except json.JSONDecodeError:
        print("Error: Could not decode JSON file.")
        return []
    
def load_dictionary(file_path):
    """
    Load words from the dictionary file into a set.
    """
    dictionary = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                words = line.strip().lower().split()
                dictionary.update(words)
    except FileNotFoundError:
        print(f"Error: Could not find file {file_path}")
    return dictionary

def get_all_corrections(word, dictionary, k=2):
    """
    Find all possible corrections for a word within edit distance k.
    Returns a list of tuples (word, distance) sorted by distance.
    """
    word = word.lower()
    if word in dictionary:
        return [(word, 0)]
    
    candidates = []
    for dict_word in dictionary:
        distance = levenshtein_distance(word, dict_word)
        if distance <= k:
            candidates.append((dict_word, distance))
    
    # Sort by edit distance and then alphabetically
    candidates.sort(key=lambda x: (x[1], x[0]))
    return candidates if candidates else [(word, 0)]

def spell_check_phrase_all_possibilities(phrase, dictionary, k=2):
    """
    Returns all possible corrections for each word in the phrase.
    """
    words = phrase.strip().split()
    all_corrections = []
    
    for word in words:
        corrections = get_all_corrections(word, dictionary, k)
        all_corrections.append(corrections)
    
    return all_corrections

def generate_correction_combinations(all_corrections, max_combinations=10):
    """
    Generate possible phrase combinations from the corrections, limited to top max_combinations.
    Returns list of (phrase, total_distance) tuples.
    """
    # Get all combinations of corrections
    combinations = list(product(*[[corr[0] for corr in word_corrs] for word_corrs in all_corrections]))
    distances = []
    
    for combo in combinations:
        total_distance = sum(min(corr[1] for corr in word_corrs if corr[0] == word) 
                           for word, word_corrs in zip(combo, all_corrections))
        distances.append((combo, total_distance))
    
    # Sort by total distance and limit results
    distances.sort(key=lambda x: x[1])
    return distances[:max_combinations]

def search_corrected_phrases(corrected_phrases, documents):
    """
    Search for all corrected phrases in the documents and return matching documents.
    """
    matching_docs = []
    for phrase, distance in corrected_phrases:
        phrase_str = ' '.join(phrase)
        for doc in documents:
            found = False
            for key in ["Title", "Author", "Bibliographic Source", "Abstract"]:
                if phrase_str.lower() in doc[key].lower():
                    matching_docs.append((doc, phrase_str, distance))
                    found = True
                    break
            if found:
                break
    return matching_docs

# Example usage:
if __name__ == "__main__":
    dictionary = load_dictionary("dictionary.txt")
    documents = load_documents("Assignment-data/bool_docs.json")
    
    test_phrase = "befroe"
    
    # Get all possible corrections for each word
    all_corrections = spell_check_phrase_all_possibilities(test_phrase, dictionary)

    # Generate and display possible combinations
    print("\nTop phrase combinations:")
    combinations = generate_correction_combinations(all_corrections)
    for phrase, total_distance in combinations:
        print(f"- {' '.join(phrase)} (total distance: {total_distance})")
    
    # Search documents with all combinations
    matching_docs = search_corrected_phrases(combinations, documents)
    
    if matching_docs:
        print("\nMatching documents:")
        for doc, phrase, distance in matching_docs:
            print(f"- Index {doc['Index']}: {doc['Title']}")
            print(f"  Matched with correction: {phrase} (distance: {distance})")
    else:
        print("\nNo matching documents found.")