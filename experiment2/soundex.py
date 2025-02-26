import json
import os
import pandas as pd
from itertools import product
import psutil
from tabulate import tabulate 

class Soundex:
    def __init__(self,filepath):
        self.dictionary=self.load_dictionary()
        self.documents=self.load_dataset(filepath)
        self.columns=["Query", "TP", "FP", "Precision", "Accuracy"]
        self.df=pd.DataFrame(columns=self.columns)
        self.correctResults=0
    
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
        
    def writeResults(self,query, corrected, suggestions):
        TP, FP= 0, 0
        for suggestion in suggestions:
            if suggestion==corrected:
                TP += 1
            else:
                FP += 1
                
        precision = TP / (TP + FP) if (TP+FP) > 0 else 0
        accuracy = TP/len(suggestions) if len(suggestions) else 0
            
        i=len(self.df)
        self.df.loc[i]=[query,TP, FP, precision, accuracy]
        if TP > 0:
            self.correctResults += 1
        
if __name__=="__main__":
    soundex=Soundex("Assignment-data/bool_docs.json")
    # for evaulation
    with open("Assignment-data/spell_queries.json") as queryFile:
        testSet=json.load(queryFile)
    with open("experiment2/soundexResults.txt","w") as file:
        for line in testSet:
            query=line['query']
        #singular runtime search
            # query=input("Enter search query:")
            suggestions=soundex.suggest_words(query)
            cleaned_suggestions=[" ".join(suggested_word) for suggested_word in suggestions]
            soundex.writeResults(query, line['corrected'],sorted(cleaned_suggestions))
            with open("experiment2/soundexResults.txt","a") as file:
                file.write(f"for {query}, did you mean: {cleaned_suggestions[:50]}\n")
        
        print(f"Precision = {(soundex.df["TP"].sum()/len(soundex.df)):.3f} | Accuracy acc to the formula= {(soundex.df["TP"].sum()/soundex.df[["TP","FP"]].sum(axis=1).sum()):.6f} | Correct Results = {soundex.correctResults}/{len(soundex.df)} | Accuracy (based on Correct Results)={soundex.correctResults/len(soundex.df)}")
        with open("experiment2/soundexResults.txt","a") as file:
            file.write("\n")
            file.write(tabulate(soundex.df,headers="keys",))
            file.write("\n")
            file.write(f"\nPrecision = {(soundex.df["TP"].sum()/len(soundex.df)):.3f} | Accuracy acc to the formula= {(soundex.df["TP"].sum()/soundex.df[["TP","FP"]].sum(axis=1).sum()):.6f} | Correct Results = {soundex.correctResults}/{len(soundex.df)} | Accuracy (based on Correct Results)={soundex.correctResults/len(soundex.df):3f}")
        # To display results during runtime
            # for suggestion in sorted(cleaned_suggestions):
            #     matchingDocs=soundex.searchDocs(suggestion)
            #     if matchingDocs:
            #         print(f"Did you mean: {suggestion}")
            #         print("Matching documents")
            #         for doc in matchingDocs:
            #             print(f"- Index {doc['Index']}: {doc['Title']}")