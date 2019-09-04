import string

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

def loadReqs(filePath):
  inFile = open(filePath, "r")

  gT = {}
  for line in inFile:
    if line != "\n" and line != "":
      line_sans_space = line.translate(str.maketrans('','',string.whitespace))
      data = line_sans_space.split( ";" )

    if len(data) == 4:
      key = addSpace(data[0])
      gT[ key ] = [data[1].split(','), data[2].split(','), data[3].split(',')]
      for k in range(len(gT[key])):
        if gT[key][k] == ['']:
          gT[key][k] = []
    else:
      print("Error Mising Semicolon:")
      print(line)
      quit()

  inFile.close()
  return gT

def loadClassInfo(filePath):
  inFile = open(filePath, "r")

  cI = {}

  for line in inFile:
    data   = line.strip().split(chr(0x1e))

    terms = []
    if len(data) == 3:
      if data[2].strip() != "":
        for term in data[2].strip().split(","):
          terms.append(term)

    if len(data) != 3 and len(data) != 2:
      print(line)
      print(data)
      quit()

    cI[data[0].strip()] = ( int(data[1].strip()), terms )

  inFile.close()
  return cI

def makeSchedulerDB(reqsDB, cI_DB, outPath):
  # We want to have the largest possible DB
  # An entry can have no reqs, if no reqs entry for it
  # However, there shouldn't be any entry with reqs, but no info

  # So first check is to make sure that all reqs have CI
  keysToDel = []
  for key in reqsDB.keys():
    if key not in cI_DB.keys():
      print("Error Couldn't find: ", key)
      keysToDel.append(key)

  for key in keysToDel:
    del reqsDB[key]


  # At this point guranteed that if in reqs, it is represented in CI
  outFile = open(outPath, "w")
  for key in cI_DB.keys():

    termList = ""
    for term in cI_DB[key][1]:
      if termList != "":
        termList += ","
      termList += term

    if termList == "":
      termList = "AUTUMN,WINTER,SPRING"

    serialize = ""
    if key in reqsDB:
      count = 0
      for cat in reqsDB[key]:
        for c in cat:
          cName = addSpace(c.translate(str.maketrans('','',string.whitespace)))
          # NOTE: We do not currently have a de-duplication Data Validation State. As such, we do pruning here
          # This check forces any and all requirments to exist in the CI DB to avoid lookup errors.
          # NOTE: This kind of a sanitization check will also probably need to be run server-side before passing in the userInput
          if "|" in c:
            print("Or Detected: ", c)
            numclasses = len(c.split("|"))
            valid = []
            for sc in c.split("|"):
              sc = addSpace(sc.translate(str.maketrans('','',string.whitespace)))

              if sc in cI_DB:
                valid.append(sc)

            # If only one entry basically becomes another AND Rel, if multiple keeps the OR, for the accepted subset
            if valid != []:
              # Need a , if this is part of a chain
              if serialize != "" and serialize[-1] != ";":
                serialize += ","
              for entry in valid:
                if serialize != "" and serialize[-1] != ";" and serialize[-1] != ",":
                  serialize += "|"
                serialize += entry
            print(serialize)
          elif cName in cI_DB:
            if serialize != "" and serialize[-1] != ";":
              serialize += ","
            serialize += cName
        count += 1
        if count < 3:
          serialize += ";"

    if serialize == "":
      serialize = ";;"

    # Key > Max Units > Term, Term > Pre ; Co ; Sup
    outFile.write( key + " > " + str(cI_DB[key][0]) + " > " + termList + " > " + serialize + "\n")


  outFile.close()


def main():
  reqsDB = loadReqs("prereq_gold.txt")
  classInfoDB = loadClassInfo("exploreCourses.db")

  makeSchedulerDB(reqsDB, classInfoDB, "fullGoldDB.db")


main()
