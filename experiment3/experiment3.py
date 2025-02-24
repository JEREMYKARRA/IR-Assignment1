from collections import defaultdict
import ijson
import os
import psutil
import time

class BSBI:
    def __init__(self,block_size):
        self.block_size=block_size
        self.block_dictionary=defaultdict(list)
        self.final_dictionary=defaultdict(list)
        
        if not os.path.exists("experiment3/writtenBlocks"):
            os.makedirs("experiment3/writtenBlocks")
        
    def parseBlocks(self):
        with open("Assignment-data/bsbi_docs.json","r") as file:
            for obj in ijson.items(file,"item"):
                docID=obj.get("Index")
                for field in ["Title","Abstract"]:
                    for word in obj[field].split():
                        self.block_dictionary[word].append(docID)

                        if len(self.block_dictionary) == self.block_size:
                            yield self.block_dictionary
                            self.block_dictionary.clear()
                    
            if self.block_dictionary:
                yield self.block_dictionary
                
    def BSBIInvert(self, block):
        postings_block=defaultdict(list)
        
        for termID, docID in sorted(block.items()):
            postings_block[termID].extend(docID)
            
        return postings_block
    
    def mergeBase(self, block1, block2):
        mergedBlock=defaultdict(list)
        
        termSet = set(block1.keys()) | set(block2.keys())
        
        for term in termSet:
            postings1 = block1.get(term,[])
            postings2 = block2.get(term,[])
            
            i,j=0,0
            mergedPostings = []
            
            while i<len(postings1) and j<len(postings2):
                if postings1[i]<postings2[j]:
                    mergedPostings.append(postings1[i])
                    i+=1
                elif postings1[i]==postings2[j]:
                    mergedPostings.append(postings1[i])
                    i+=1
                    j+=1
                else:
                    mergedPostings.append(postings2[j])
                    j += 1
                    
            mergedPostings.extend(postings1[i:])
            mergedPostings.extend(postings2[j:])
            
            mergedBlock[term]=mergedPostings
        
        return mergedBlock
        
    def mergeRecursive(self, blocks, left, right):
            if left==right:
                return self.readBlock(blocks[left])
            
            if left+1==right:
                block_1=self.readBlock(blocks[left])
                block_2=self.readBlock(blocks[right])
                return self.mergeBase(block_1,block_2)
            
            middle=(left+right)//2
            left_block=self.mergeRecursive(blocks,left,middle)
            right_block=self.mergeRecursive(blocks,middle+1,right)
            
            return self.mergeBase(left_block,right_block)
    
    def mergeBlocks(self,dirpath):
        
        blocks = [file for file in os.listdir(dirpath) if file.startswith("block") and file.endswith('.txt')]
        
        blocks.sort()
        self.final_dictionary=self.mergeRecursive(blocks,0,len(blocks)-1)
        
        #write final_dictionary to file_out
        with open(f"experiment3/writtenBlocks/blockMerged.txt","w+") as dict_out:
            for term, postings in sorted(self.final_dictionary.items()):
                dict_out.write(f"{term}:{','.join(map(str, postings))}\n")
            
    def writeBlockToDisk(self,blockID,postings_block):
        with open(f"experiment3/writtenBlocks/block{blockID}size{self.block_size}.txt","w+") as file_out:
            for term, postings in sorted(postings_block.items()):
                file_out.write(f"{term}:{','.join(map(str, postings))}\n")
            
    def readBlock(self, filepath):
        block=defaultdict(list)
        with open(os.path.join("experiment3/writtenBlocks/",filepath),"r") as file:
            for line in file:
                term, postings = line.strip().split(":",1)
                block[term] = postings.split(",") if postings else []
        return block
    
    def BSBIndexConstruction(self):
        start_time=time.time()
        process=psutil.Process(os.getpid())
        
        init_mem=process.memory_info().rss / (1024 * 1024)
        
        i=0
        for block in self.parseBlocks():
            postings_block=self.BSBIInvert(block)
            self.writeBlockToDisk(i,postings_block)
            i += 1
        
        self.mergeBlocks("experiment3/writtenBlocks")
        
        final_mem=process.memory_info().rss / (1024 * 1024)
        end_time=time.time()
        
        time_taken=end_time-start_time
        mem_used=final_mem-init_mem
        
        print(f"Block Size: {self.block_size} | Time Taken: {time_taken:.2f} sec | Memory Used: {mem_used:.2f} MB\n")

if __name__=="__main__":
    for block_size in [200,10000]:
        bsbi=BSBI(block_size)
        bsbi.BSBIndexConstruction()
    