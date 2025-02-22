from itertools import product

class Soundex:
    def __init__(self):
        self.dictionary=self.load_dictionary()
    
    def load_dictionary(self):
        with open("IR-Assignment-1/dictionary.txt","r") as file:
            dictionary=[line.strip() for line in file]
            return dictionary        

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
            
        
if __name__=="__main__":
    query=input("Enter search query:")
    suggestions=Soundex().suggest_words(query)
    cleaned_suggestions=[" ".join(suggested_word) for suggested_word in suggestions]
    print(f"Did you mean any of these: {', '.join(sorted(cleaned_suggestions))}")

#add bool ret
