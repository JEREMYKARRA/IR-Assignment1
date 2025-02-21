import re
import json

def extract_words_from_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    words = set()
    for doc in data:
        for key in ["Title", "Author", "Bibliographic Source", "Abstract"]:
            if key in doc:
                words.update(re.findall(r'\b[a-zA-Z]+\b', doc[key].lower()))
    
    return sorted(words)

json_file = "IR-Assignment-1/Assignment-data/bool_docs.json" # put in the correct path for bool_docs.json
dictionary = extract_words_from_json(json_file)

with open("dictionary.txt", "w", encoding="utf-8") as f:
    for word in dictionary:
        f.write(word + "\n")

print("Dictionary extracted and saved successfully.")
print(len(dictionary))
print(dictionary[:10])