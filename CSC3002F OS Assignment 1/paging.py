from queue import Queue
import queue
import sys
import random

def FIFO(size,pages):
    window = Queue()
    check = set()
    page_faults = 0
    for i in range(len(pages)) :
        if(len(check) < size):
            if(pages[i] not in check):
                page_faults+=1
                check.add(pages[i])
                window.put(pages[i])

        else:
            if(pages[i] not in check):
                page_faults+=1

                temp = window.queue[0]
                window.get()

                check.remove(temp)
                check.add(pages[i])
                window.put(pages[i])
    return page_faults

# def LRU(size,pages):
#     page_faults = 0
#     window = []

#     for i in range(len(pages)):
#         if(pages[i] not in window):
#             if(len(window) == size):
#                 window.remove(window[0])
#                 window.append(pages[i])
#             else:
#                 window.append(pages[i])
#             page_faults+=1
#         else:
#             window.remove(pages[i])
#             window.append(pages[i])

#     return page_faults

def LRU(size,pages):
    clock = 0
    window = {}
    page_faults = 0
    for i in range(len(pages)):
        if(len(window)<size):
            window[pages[i]] = clock
            page_faults += 1
            # ages.append(clock)
        else:
            if(pages[i] not in window):
                page_faults += 1
                oldest = min(window, key = window.get)
                window.pop(oldest)
                window[pages[i]] = clock
            else:
                window[pages[i]] = clock
        clock +=1
    return page_faults

def OPT(size,pages):
    window = []
    page_faults = 0 
    for i in range(len(pages)):
        if(len(window)<size):
            window.append(pages[i])
            page_faults += 1
        else:
            if(pages[i] not in window):
                page_faults += 1
                distances = []
                no_future = False
                for future in range(len(window)):
                    if(window[future] not in pages[i:]):
                        window[future] = pages[i]
                        no_future = True
                    else:
                        distances.append(pages.index(window[future]))
                if(not no_future):
                    window[distances.index(max(distances))] = pages[i]    
                    
               
           
        
    return page_faults

def main():
    pages = []
    pages = [random.randint(0,9) for i in range(10000)] 
    size = int(sys.argv[1])
    print ("FIFO", FIFO(size,pages), "page faults.")
    print ("LRU", LRU(size, pages), "page faults.")
    print ("OPT", OPT(size, pages), "page faults.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print ("Usage: python paging.py[number of pages]")
    else:
        main()


