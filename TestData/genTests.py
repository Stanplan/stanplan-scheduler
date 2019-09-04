import json

def makeTestJson( courseDict, minUnits, maxUnits, force, summer, outputName = "test", testNumber = 1):
  # Sample Web Output:
  # {"courses":[{"code":"CS 148","units":5},{"code":"CS 154","units":3},{"code":"CS 157","units":3},{"code":"CS 156","units":5},{"code":"CS 106A","units":5}],"minUnitsPerQuarter":12,"maxUnitsPerQuarter":22,"scheduleInSummer":true,"considerPrereqs":true}
  tempJson = json.loads("{}")

  tempJson["minUnitsPerQuarter"]  = minUnits
  tempJson["maxUnitsPerQuarter"]  = maxUnits
  tempJson["scheduleInSummer"]    = summer
  tempJson["considerPrereqs"]     = force

  tempJson["courses"] = []
  index = 0
  for course in courseDict:
    tempJson["courses"].append({})
    tempJson["courses"][index]["code"]   = course
    tempJson["courses"][index]["units"]  = courseDict[course]
    index += 1

  outFile = open(outputName + str(testNumber) + ".json", "w")
  outFile.write(json.dumps(tempJson, indent=2, sort_keys=True, ensure_ascii=True) )
  outFile.close()

def makeTestDB( courseDict, outputName = "test", testNumber = 1):
  outFile = open(outputName + str(testNumber) + ".db", "w")
  for entry in courseDict:
    outFile.write(entry + " > " + str(courseDict[entry][0]) + " > " + courseDict[entry][1] + " > " + courseDict[entry][2] + "\n")
  outFile.close()
    

def makeTest1():
  userInput = { "CS 107" : 3,
                "CS 109" : 2
                }

  courseDB  = { "CS 107" : (7, "AUTUMN, SPRING", "CS 109, CS 106;;"),
                "CS 109" : (6, "AUTUMN, SPRING", "CS 106;;"),
                "CS 106" : (5, "AUTUMN, SPRING", ";;")
              }

  makeTestJson( userInput, 1, 20, True, True )
  makeTestDB( courseDB )

def makeTest2():
  userInput = { "CS 107" : 3,
                "CS 109" : 2,
                "CS 100" : 2,
                }

  courseDB  = { "CS 107" : (7, "AUTUMN, SPRING", "CS 106|CS 100, CS 109;;"),
                "CS 109" : (6, "AUTUMN, SPRING", "CS 106;;"),
                "CS 106" : (5, "AUTUMN, SPRING", ";;"),
                "CS 100" : (5, "AUTUMN, SPRING", ";;"),
                "CS 105" : (5, "AUTUMN, SPRING", ";;"),
              }

  makeTestJson( userInput, 1, 20, True, True, testNumber = 2 )
  makeTestDB( courseDB, testNumber = 2 )

def makeTest3():
  userInput = { "CS 109" : 3,
                }

  courseDB  = { "CS 107" : (7, "AUTUMN, SPRING", "CS 106|CS 100;;"),
                "CS 109" : (6, "AUTUMN, SPRING", "CS 107;;"),
                "CS 106" : (5, "AUTUMN, WINTER, SPRING", ";;"),
                "CS 100" : (5, "AUTUMN, SPRING", ";;"),
                "CS 105" : (5, "AUTUMN, SPRING", ";;"),
              }

  makeTestJson( userInput, 1, 20, True, True, testNumber = 3 )
  makeTestDB( courseDB, testNumber = 3 )

def makeTest4():
  userInput = { "CS 115" : 3,
                }

  courseDB  = { "CS 101" : (7, "AUTUMN, SPRING", ";;"),
                "CS 102" : (6, "SPRING", "CS 101;;"),
                "CS 103" : (5, "WINTER", "CS 102;;"),
                "CS 104" : (5, "Spring", "CS 103;;"),
                "CS 115" : (5, "Spring", "CS 104;;"),
              }

  makeTestJson( userInput, 1, 20, True, True, testNumber = 4 )
  makeTestDB( courseDB, testNumber = 4 )

def makeTest5():
  userInput = { "CS 107" : 15,
                "CS 109" : 7,
                "CS 100" : 19,
                }

  courseDB  = { "CS 107" : (7, "AUTUMN, SPRING", "CS 106|CS 100, CS 109;;"),
                "CS 109" : (6, "AUTUMN, SPRING", "CS 106;;"),
                "CS 106" : (5, "AUTUMN, SPRING", ";;"),
                "CS 100" : (5, "AUTUMN, SPRING", ";;"),
                "CS 105" : (5, "AUTUMN, SPRING", ";;"),
              }

  makeTestJson( userInput, 1, 20, True, True, testNumber = 5 )
  makeTestDB( courseDB, testNumber = 5 )

def makeTest6():
  userInput = { "CS 107" : 15,
                "CS 109" : 7,
                "CS 100" : 1,
                }

  courseDB  = { "CS 107" : (7, "AUTUMN, SPRING", "CS 106|CS 100, CS 109;;"),
                "CS 109" : (6, "AUTUMN, SPRING", "CS 106;;"),
                "CS 106" : (5, "AUTUMN, SPRING", ";;"),
                "CS 100" : (5, "AUTUMN, SPRING", ";;"),
                "CS 105" : (5, "AUTUMN, SPRING", ";;"),
              }

  makeTestJson( userInput, 1, 20, True, True, testNumber = 6 )
  makeTestDB( courseDB, testNumber = 6 )

def makeTest7():
  userInput = { "CS 107" : 1,
                }

  courseDB  = { "CS 107" : (7, "AUTUMN, SPRING", "CS 106|CS 100, CS 109; CS 105;"),
                "CS 109" : (6, "AUTUMN, SPRING", "CS 106;;"),
                "CS 106" : (5, "AUTUMN, SPRING", ";;"),
                "CS 100" : (5, "AUTUMN, SPRING", ";;"),
                "CS 105" : (5, "AUTUMN, SPRING", "CS 104;;"),
                "CS 104" : (19, "AUTUMN, SPRING", ";;"),
              }

  makeTestJson( userInput, 1, 20, True, True, testNumber = 7 )
  makeTestDB( courseDB, testNumber = 7 )

def makeTest8():
  userInput = { "CS 107" : 1,
                }

  courseDB  = { "CS 107" : (7, "AUTUMN, SPRING", "CS 106|CS 100; CS 109|CS 101, CS 105;"),
                "CS 109" : (6, "AUTUMN, SPRING", "CS 106;;"),
                "CS 106" : (5, "AUTUMN, SPRING", ";;"),
                "CS 100" : (5, "AUTUMN, SPRING", ";;"),
                "CS 101" : (5, "AUTUMN, SPRING", ";;"),
                "CS 105" : (5, "AUTUMN, SPRING", "CS 104;;"),
                "CS 104" : (19, "AUTUMN, SPRING", ";;"),
              }

  makeTestJson( userInput, 1, 20, True, True, testNumber = 8 )
  makeTestDB( courseDB, testNumber = 8 )

def makeTest9():
  # {"courses":[{"code":"CS 148","units":5},{"code":"CS 154","units":3},{"code":"CS 157","units":3},{"code":"CS 156","units":5},{"code":"CS 106A","units":5}],"minUnitsPerQuarter":12,"maxUnitsPerQuarter":22,"scheduleInSummer":true,"considerPrereqs":true}
  userInput =  {  "CS 148"  : 5,
                  "CS 154"  : 3,
                  "CS 157"  : 3,
                  "CS 156"  : 5,
                  "CS 106A" : 5
                  }

  makeTestJson( userInput, 1, 20, True, True, testNumber = 9 )
  # Uses the fullGoldDB.db, so no test DB generated

  
# Start and End Nums are inclusive for this function
def genTests(startNum, endNum):
  for num in range(startNum, endNum + 1):
    eval("makeTest"+str(num)+"()")

genTests(1, 9)
#makeTest9()

