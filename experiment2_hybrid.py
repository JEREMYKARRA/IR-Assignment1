import json
import os
from itertools import product
import psutil

class EditSoundex:
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
            
            self.spell_check_phrase_all_possibilities(term,suggestions_per_word)
                
            
    
    def levenshtein_distance(self,str1, str2):
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
            
    def get_all_corrections(self,word, k=2):
        word = word.lower()
        if word in self.code_list:
            return [(word, 0)]
        
        candidates = []
        for dict_word in self.code_list:
            distance = self.levenshtein_distance(word, dict_word)
            if distance <= k:
                candidates.append((dict_word, distance))
        
        # Sort by edit distance and then alphabetically
        candidates.sort(key=lambda x: (x[1], x[0]))
        return candidates if candidates else [(word, 0)]
            
    def searchDocs(self,permutation):
        matchingDocs={}
        
        for doc in self.documents:
            for key in ["Title", "Author", "Bibliographic Source", "Abstract"]:
                if permutation.lower() in doc[key].lower():
                    matchingDocs[doc["Index"]]=doc
                            
        return list(matchingDocs.values()) if matchingDocs else None
    
    def spell_check_phrase_all_possibilities(self, phrase, k=2):
        words = phrase.strip().split()
        all_corrections = []
        
        for word in words:
            corrections = self.get_all_corrections(word,k)
            all_corrections.append(corrections)
        
        return all_corrections

    def generate_correction_combinations(self,all_corrections, max_combinations=10):
        combinations = list(product(*[[corr[0] for corr in word_corrs] for word_corrs in all_corrections]))
        distances = []
        
        for combo in combinations:
            total_distance = sum(min(corr[1] for corr in word_corrs if corr[0] == word) 
                            for word, word_corrs in zip(combo, all_corrections))
            distances.append((combo, total_distance))
        
        # Sort by total distance and limit results
        distances.sort(key=lambda x: x[1])
        return distances[:max_combinations]
        
if __name__=="__main__":
    query=input("Enter search query:")
    editSoundex=EditSoundex("Assignment-data/bool_docs.json")
    
