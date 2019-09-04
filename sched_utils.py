import string
import json
import os

def isInt(num):
  try:
    int(num)
    return True
  except ValueError:
    return False

# For dealing with course codes that don't have a space between dept and #
def addSpace(className):
    index = 0
    while className[index] not in string.digits and className[index] != " ":
        index += 1
        if index >= len(className):
            print("Error Exceeded Bound no #")
            # NOTE: May want to make this scream louder:
            # quit() # TOO Loud?
            break

    # Already had a space, all is already well
    if className[index] == " ":
      return className.strip()

    # Not at the end and no space, time to insert space
    if index < len(className):
        first  = className[0 : index]
        #print("First:", first)
        second = className[index :  ]
        #print("Second:", second)
        newClass = first + " " + second
        #print(newClass)
        return newClass.strip() #, first, second

    # When this is expected to give first and second, the repetition is the closest aproximation, but the answer is kind of non-sensical
    return className.strip() #, className, className

def outputServerSchedule(schedule, outPath):
  fileDir = os.path.dirname(os.path.realpath('__file__'))
  filename = os.path.join(fileDir, './' + outPath)
  outFile = open(filename, "w")
  outputJSON = json.loads("[]")
  index = 0
  for year in schedule:
    hasClasses = False
    for term in schedule[year]:
      if schedule[year][term].hasClasses():
        hasClasses = True
    if hasClasses:
      outputJSON.append({})
      outputJSON[index]["year"]     = year
      outputJSON[index]["quarters"] = []
      index_2 = 0
      for term in ["AUTUMN", "WINTER", "SPRING", "SUMMER"]:
        if term in schedule[year]:
          outputJSON[index]["quarters"].append({})
          outputJSON[index]["quarters"][index_2]["quarter"] = schedule[year][term].term
          outputJSON[index]["quarters"][index_2]["units"]   = schedule[year][term].curUnits
          outputJSON[index]["quarters"][index_2]["courses"] = []
          s_index = 0
          for key in schedule[year][term].courseDict:
            outputJSON[index]["quarters"][index_2]["courses"].append({})
            outputJSON[index]["quarters"][index_2]["courses"][s_index]["code"]   = key
            outputJSON[index]["quarters"][index_2]["courses"][s_index]["units"]  = schedule[year][term].courseDict[key]
            s_index += 1
          index_2 += 1
      index += 1


  outFile.write(json.dumps(outputJSON, indent=2, sort_keys=True, ensure_ascii=True) )
  outFile.close()
