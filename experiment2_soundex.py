import json
import os
from itertools import product
import psutil

class Soundex:
    def __init__(self,filepath):
        self.dictionary=self.load_dictionary()
        self.documents=self.load_dataset(filepath)
    
    def load_dictionary(self):
        with open("dictionary.txt","r") as file:
            dictionary=[line.strip() for line in file]
            return dictionary
    
    def load_dataset(self, filepath):
        with open(filepath,"r") as dataset:
            return json.load(dataset)

    def soundex_tokenize(self,query):
        query=query.upper().split()        
        return [self.generate_soundex_code(term) for term in query]
        
    def generate_soundex_code(self, term):
        term=term.upper()
        soundex=term[0]
        
        soundex_dictionary={"BFPV":"1","CGJKQSXZ":"2","DT":"3","L":"4","MN":"5","R":"6","AEIOUHWY":"0"}
        
        for t in term[1:]:
            for key in soundex_dictionary.keys():
                if t in key:
                    code=soundex_dictionary[key]
                    if code!="0" and code!=soundex[-1]:
                        soundex+=(code)
                    
        return soundex[:4].ljust(4,"0")
        
    def suggest_words(self,query):
        code_list=self.soundex_tokenize(query)
        suggestions=[]
        for term in code_list:
            suggestions_per_word=[]
            suggestions_per_word={word for word in self.dictionary if self.generate_soundex_code(word.upper())==term}
            suggestions.append(suggestions_per_word)
            
        permutations=list(product(*suggestions))
            
        return permutations
            
    def searchDocs(self,permutation):
        matchingDocs={}
        
        for doc in self.documents:
            for key in ["Title", "Author", "Bibliographic Source", "Abstract"]:
                if permutation.lower() in doc[key].lower():
                    matchingDocs[doc["Index"]]=doc
                            
        return list(matchingDocs.values()) if matchingDocs else None
        
if __name__=="__main__":
    
    query=input("Enter search query:")
    soundex=Soundex("Assignment-data/bool_docs.json")
    suggestions=soundex.suggest_words(query)
    cleaned_suggestions=[" ".join(suggested_word) for suggested_word in suggestions]
    for suggestion in sorted(cleaned_suggestions):
        matchingDocs=soundex.searchDocs(suggestion)
        if matchingDocs:
            print(f"Did you mean: {suggestion}")
            print("Matching documents")
            for doc in matchingDocs:
                print(f"- Index {doc['Index']}: {doc['Title']}")