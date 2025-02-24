from collections import defaultdict
import ijson
import os
import psutil
import spacy
import time

#benchmarking

class BooleanRetrieval:
    def __init__(self, filepath):
        self.documents={}
        self.initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        self.invertedIndex=defaultdict(lambda:{"df":0,"docs":set()})
        self.nlp=spacy.load("en_core_web_sm")
        start_time=time.time()
        
        self.build_index(filepath)
        
        end_time=time.time()
        self.current_memory = psutil.Process().memory_info().rss / (1024*1024)
        
        elapsedTime=end_time-start_time
        usedMemory=self.current_memory-self.initial_memory
        
        print(f"Inverted Index Construction\nTime taken: {elapsedTime:.2f} sec | Memory used: {usedMemory:.2f} MB")
    
    def tokenize(self,text):
        doc=self.nlp(text)
        return [token.lemma_ for token in doc if token.is_alpha and not token.is_stop and not token.is_punct]

    def load_dataset(self, filepath):
        with open(filepath,"r",encoding="utf-8") as dataset:
            for obj in ijson.items(dataset,'item'):
                yield{
                    "Index": obj["Index"],
                    "Title":obj.get("Title",""),
                    "Author":obj.get("Author",""),
                    "Bibliographic Source":obj.get("Bibliographic Source",""),
                    "Abstract":obj.get("Abstract",""),
                }

    def build_index(self,filepath):
        
        for obj in self.load_dataset(filepath):
            obj_id=obj["Index"]
            self.documents[obj_id]=obj
            fields=[obj["Title"],obj["Author"],obj["Bibliographic Source"],obj["Abstract"]]
            distinct_terms=set()
            
            for field_text in fields:
                words=self.tokenize(field_text)
                for word in words:
                    self.invertedIndex[word]["docs"].add(obj_id)
                    distinct_terms.add(word)
                
            for term in distinct_terms:
                self.invertedIndex[term]["df"]+=1
        
        return {word: {"docs":list(data["docs"]),"df":data["df"]} for word, data in self.invertedIndex.items()}

    def writeInvertedIndexToFile(self):
        with open("exp1_inverted_index.txt","w+") as file_out:
            for term in sorted(self.invertedIndex.keys()):
                data=self.invertedIndex[term]
                file_out.write(f"{term} -> df: {data['df']} | docs: {', '.join(map(str, sorted(data['docs'])))}\n")

    def retrieve(self, query):
        start_time=time.time()
        initial_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        
        terms=query.split()
        term_stack=[]
        operator_stack=[]
        
        universe=set().union(*[data["docs"] for data in self.invertedIndex.values()])
        
        def apply_bool():
            bool_op=operator_stack.pop()
            
            if bool_op=="NOT":
                term=term_stack.pop()
                term_stack.append(universe-term)
            else:
                right_term=term_stack.pop()
                left_term=term_stack.pop()
                if bool_op=="AND":
                    term_stack.append(left_term & right_term)
                elif bool_op=="OR":
                    term_stack.append(left_term | right_term)
                
        
        for term in terms:
            if term in {"AND", "OR", 'NOT'}:
                    operator_stack.append(term)
            elif term=="(":
                operator_stack.append(term)
            elif term==")":
                while operator_stack and operator_stack[-1]!="(":
                    apply_bool()
                operator_stack.pop()
            else:
                term_set=self.invertedIndex.get(term,{}).get("docs",set())
                term_stack.append(term_set)
            
        while operator_stack:
            apply_bool()
            
        end_time=time.time()
        current_memory = psutil.Process().memory_info().rss / (1024*1024)

        timeElapsed=end_time-start_time
        usedMemory=current_memory-initial_memory

        print(f"Query Retrieval\nTime Taken: {timeElapsed:.2f} sec | Memory used: {usedMemory:.2f} MB")

            
        return term_stack.pop() if term_stack else set()
    
    def display_results(self, doc_ids):
        for doc_id in sorted(doc_ids):
            doc =self.documents.get(doc_id, {})
            print(f"Title: {doc.get('Title', 'N/A')}\n"
                    f"Author: {doc.get('Author', 'N/A')}\n"
                    f"Bibliographic Source: {doc.get('Bibliographic Source', 'N/A')}\n"
                    f"Abstract: {doc.get('Abstract', 'N/A')}\n"
            )

if __name__=="__main__":
    filename="Assignment-data/bool_docs.json"
    bronze_retrieve=BooleanRetrieval(filename)
    bronze_retrieve.writeInvertedIndexToFile()
    query=input("Enter a term to search: ")
    
    relevant_docs=bronze_retrieve.retrieve(query)
    if relevant_docs:
        print(f"These are the relevant docs: {sorted(relevant_docs)}")
        bronze_retrieve.display_results(relevant_docs)
    else:
        print(f"Sorry no documents found for {query}")