#################################################################################################################################################
import csv

# prog 1 imports
import difflib as dl
import multiprocessing as mp
from multiprocessing.sharedctypes import Value
import ctypes
import time

# prog 2 imports
import os
import networkx as nx
#################################################################################################################################################


#################################################################################################################################################
# Function used to import station data into a list USED FOR 1ST PROGRAM FUNCTION
def importData1():
    
    count = 0
    stations = []
    with open("data/railway_stations.csv", "r") as stationdata:
        
        # setting reader and looping through file
        reader = csv.reader(stationdata, delimiter=",", skipinitialspace=True)
        for row in reader:
            
            if count == 0: # ignores the first line of csv to allow for headings
                count+=1
            else:
                stations.append(row) # appending rows to station list
    
    return stations # returning sorted station list


# Function used to import network data into 2 lists USED FOR 2ND PROGRAM FUNCTION
def importData2():
    
    network = []
    with open("data/railway_network.csv", "r") as networkdata:
        
        # setting reader and looping through file
        reader = csv.reader(networkdata, delimiter=",", skipinitialspace=True)
        for row in reader:
            network.append((row[0].upper(), row[1].upper(), row[2])) # appending rows to network list
              
    return network # returning network list
#################################################################################################################################################


#################################################################################################################################################
# function used to run program 1      
def task1Search(data):
    searchitem = data[0]
    stations = data[1][1]
    start = data[2]
    end = data[3]
    found = Value(ctypes.c_bool, False)
    bestmatch = []
    # task 1.1
    for i in range(start, end):
        
        if stations[i][0] == searchitem: # Finding CRS from station name
            found.value = True
            print("Found: " + str(stations[i][1]) + ", in position: " + str(i))
            break
        
        elif stations[i][1] == searchitem: # Finding station name from CRS
            found.value = True
            print("Found: " + str(stations[i][0]) + ", in in position: " + str(i))
            break
        
        # task 1.2
        else: # Else look for keywords or similarities
            
            keywords = stations[i][0].split() # Split item into keywords
            for j in range(len(keywords)):
                
                if keywords[j] == searchitem: # Check to see if keyword match present
                    found.value = True
                    print("Found Search Item: " + str(stations[i][0] +", "+stations[i][1]))
                
                else: # If no keyword match is found look for close matches
                    ratio = dl.SequenceMatcher(None, searchitem, keywords[j]).ratio()
                    if ratio > 0.8: # If match ratio above 75% add to bestmatch list
                        bestmatch.append(stations[i])     
    
    
    # time.sleep(0.3) # sleep command added to wait for parallel procs to finish                              
    if len(bestmatch) > 0 and found.value == False: # If item couldnt be found and no keywords match then print the best fit
        for j in range(len(bestmatch)):
            
            print("Found Best Match: " + str(bestmatch[j][0] +", "+ bestmatch[j][1]))
            
        return 1

    elif found == False: # Only triggered if item isnt found and there are no best matches
        print("Search Item Not Found!")
        return -1


# function for multiple search from file
def task1MultiSearch(data):
    
    testdata = data[0]
    sortedcrs = data[1][0] # set of stations sorted by crs code
    sortedname = data[1][1] # set of stations sorted by station name
    start = data[2] # start position
    end = data[3] # end position
    
    # looping through the test set in shared memory
    for j in range(len(testdata)):
        
        # setting left and right positions to the start and end points (resets each test data)
        left = start
        right = end
        
        # if search item is a CRS code (3 characters and upper case)
        if len(testdata[j][0]) == 3 and testdata[j][0].isupper():
            
            # binary search through sorted crs list, appends missing data if found
            while left <= right:
                
                mid = (left+right) // 2
                
                if sortedcrs[mid][1] == testdata[j][0]:
                    testdata[j] = [sortedcrs[mid][0], testdata[j][0]]
                    break
                
                if sortedcrs[mid][1] < testdata[j][0]:
                    left = mid + 1
                
                elif sortedcrs[mid][1] > testdata[j][0]:
                    right = mid - 1
                    
        # if search item is a name   
        else:
            
            # binary search through sorted name list, appends missing data if found
            while left <= right:
                
                mid = (left+right) // 2
                
                if sortedname[mid][0] == testdata[j][0]:
                    testdata[j] = [testdata[j][0], sortedname[mid][1]]
                    break
                
                if sortedname[mid][0] < testdata[j][0]:
                    left = mid + 1
                
                elif sortedname[mid][0] > testdata[j][0]:
                    right = mid - 1
    
    
# task1.3 parallelization (parallel through search)
def sProc(search, testdata, stations, type):
                 
        data = []
        pool = mp.Pool()
        
        # if a singular search item is given
        if type == "singular":
            
            # computing start and end positions for 4 processes (4 cores)
            for i in range(4):
                
                startPos = round(i * len(stations[0]) / 4)
                endPos = round((i+1) * len(stations[0]) / 4)
                data.append((search, stations, startPos, endPos))
            
            # creating processes with separate data with target single data search function
            pool.map(task1Search, [data[0], data[1], data[2], data[3]])
            
            pool.close()
            pool.join()
        
        # if bulk data is given
        elif type == "multiple":
            
            # computing start and end positions for 4 processes (4 cores)
            for i in range(4):
                
                startPos = round(i * len(stations[1]) / 4)
                endPos = round((i+1) * len(stations[1]) / 4)
                data.append((testdata, stations, startPos, endPos))
            
            # creating processes with separate data with target multi data entry search function
            pool.map(task1MultiSearch, [data[0], data[1], data[2], data[3]])
                  
            pool.close()
            pool.join()
            
            
    
def runProg1():
    # RUNNING CODE FOR PROGRAM 1 #  
    funct = input("\nPlease enter 1 for singular search or 2 to use the testing file: ")
    
    if funct != "1" and funct != "2":
        
        print("\nPlease enter either 1 or 2 to continue.")
        runProg1()
        
    else:
        
        # defining manager and shared memory for stations and testdata
        manager = mp.Manager()
        testdata = manager.list()
        
        # creating two lists in shared memory one sorted by CRS code, one sorted by name
        sortedcrs = manager.list(sorted(importData1(), key=lambda x:x[1]))
        sortedname = manager.list(sorted(importData1(), key=lambda x:x[0]))
        
        # both lists are passed to the functions in a tuple
        stations = ((sortedcrs, sortedname))
        
        # looping through testfile and retrieving test data (file must be called "test_file.csv")
        with open("data/test_file.csv", "r") as stationdata:
            reader = csv.reader(stationdata, delimiter=",", skipinitialspace=True)
            for row in reader:
                testdata.append(row)
        
        # checks if first or second function has been selected
        if funct == "1":
            
            search = (input("Enter search item: ")) # retrieves search data from user
            sProc(search, testdata, stations, "singular")
            
        else:
            
            search = 0 # no search data as bulk data is read from file
            
            # recording time data and calling process creation
            start_time = time.time()
            sProc(search, testdata, stations, "multiple")
            end_time = time.time()
            
            # printing out the results of the bulk data entry tests and writing to a file in data folder
            f = open("data/test_results.csv", "w")
            writer = csv.writer(f)
            
            for i in range(len(testdata)):
                print("Test " + str(i+1) + " Result: " + str(testdata[i][0] + ", "+ str(testdata[i][1])))
                row = [str(testdata[i][0]) +", " + str(testdata[i][1])]
                writer.writerow(row)
            
            # printing time taken to create processes and run search
            print("Function completed " + str(len(testdata)) + " tests in: " + str(end_time - start_time) + " seconds.")   
            
            f.close() # closing file
#################################################################################################################################################   
        
        
#################################################################################################################################################
# function used to run program 2 
def runProg2():
    
    # function to create a networkx graph object from nodes and edges lists
    def createGraph():
        network = importData2() # importing data
        G = nx.Graph() # creating graph object
        edges = []
        # looping through network and adding edges to list with weight in separate dict
        for i in range(len(network)):
            edges.append((network[i][0], network[i][1], {"weight" : int(network[i][2])}))
            
        # adding edges from list (nodes added automatically) 
        G.add_edges_from(edges)
        
        print(G)
        
        return G # returning graph 
    
    
    # function to find the lowest cost route between two stations
    def task2_1(graph):
        # retrieving both nodes from user input
        print("\nPlease enter station names for the starting and ending nodes: ")
        node1 = input("Starting Station: ").upper()
        node2 = input("Ending Station: ").upper()
        
        # try except to catch error if station entered cannot be matched with a node
        try:
            # finding dijkstra algo shortest path between points
            path = nx.dijkstra_path(graph, source=node1, target=node2, weight="weight")
            # calculating weight of total path
            accweight = nx.path_weight(graph, path, weight="weight")
            
            # printing data back to user
            print("\nPath Taken: ")
            print(path)
            print("Cost: " + str(accweight))
            
        except:
            # print error if station name cannot be matched and re-run function
            print("\nError: Station name not recognised!")
            task2_1(graph)
        
        
    # function to find the lowest cost route visiting all stations
    def task2_2(graph):
        cumulativeWeight = 0 # set cumulative weight
        # find shortest path between all nodes
        path = nx.minimum_spanning_edges(graph, algorithm="kruskal", weight="weight", data=True)
        # loop through path and find sum of weights of edges
        for p in path:
            cumulativeWeight+= p[2]["weight"]
            
        # print output to the user
        print("\nCumulative Cost to visit all stations: ")
        print(cumulativeWeight)
        
        
    # RUNNING CODE FOR PROGRAM 2 #  
    funct = input("\nEnter 1 for shortest path between stations (2.1) or 2 for shortest path to connect all stations (2.2): ")
    if funct != "1" and funct != "2":
        print("\nPlease enter either 1 or 2 to continue.")
        runProg2()
        
    else:
        # imports and graph creation
        graph = createGraph()
        if funct == "1":
            task2_1(graph)
        else:
            task2_2(graph)
#################################################################################################################################################


################################################################################################################################################# 
# function used to call at end asking user for continuation
def callContinue():
    interfaceContinue = input("\nRe-run Program (Y/N): ").upper()
    if interfaceContinue != "N" and interfaceContinue != "Y":
        print("\nPlease enter either Y to continue or N to end.")
        callContinue()
    else:
        if interfaceContinue == "Y":
            return True
        else:
            return False

# function used to choose either program 1 or program 2 
def chooseProg():
    prog = input("\nPlease enter 1 for station searching (Program 1) or 2 for station networking (Program 2): ")
    if prog != "1" and prog != "2":
            print("\nPlease enter either 1 or 2.")
            chooseProg()
    elif prog == "1":
        runProg1()
    else:
        runProg2()
        
# sequential code for main process
if __name__ == "__main__":
    
    os.system("pip install networkx")
    
    interface = True
    while interface == True:
        chooseProg()
        interface = callContinue()
#################################################################################################################################################   
    
    
    
    
        
    
    
    
    