import indirect_scheduler as sched
import sched_utils as su
import json

# For Parameter Loading
import argparse
import sys

# Setup the Argument Parser
# For More on how this works, see the docs at: https://docs.python.org/3/library/argparse.html
parser = argparse.ArgumentParser(description='Scheduler Parameters')

# Location of Train Data
parser.add_argument("-db_path",           type=str, default='Data/fullGoldDB.db',     help="Path to the Courses Information Database (Units, Terms, Reqs). Default Path: ./Data/fullGoldDB.db")
parser.add_argument("-userInput",         type=str, default='TestData/test9.json',    help="Path to the user's course selection. Default Path: ./TestData/test9.json. Note: This value was chosen for testing.")
parser.add_argument("-outputPath",        type=str, default='Data/output.json',            help="Path for where we should output the schedule json. Default Path: ./output.json")

# Parse the args and generate the params, so that we can access them
params, _ = parser.parse_known_args()

# Parameters passed, and all parameters
print('\ntogrep : {0}\n'.format(sys.argv[1:]))
print(params)

def printSched(schedule):
  for key in schedule:
    for sk in schedule[key]:
      print(key, sk, ":")
      schedule[key][sk].output()

def outputSimpleSchedule(schedule, outPath):
  #outFile = open(outPath, "w")
  #outFile.write(json.dumps(schedule, indent=2, sort_keys=True, ensure_ascii=True) )
  #outFile.close()

  outFile = open(outPath, "w")
  outputJSON = json.loads("{}")
  for key in schedule:
    outputJSON[key] = {}
    for sk in schedule[key]:
      outputJSON[key][sk] = schedule[key][sk].courseDict

  outFile.write(json.dumps(outputJSON, indent=2, sort_keys=True, ensure_ascii=True) )
  outFile.close()

def main():
  #sched.loadDB("TestData/test8.db")
  sched.loadDB(params.db_path)

  userChoices, maxUnits, minUnits, useSummer, forcePre = sched.jsonToCourseList(params.userInput)

  userChoices = sched.pruneUserChoices(userChoices)

  # Could return keyToNode, codeToKey, nodesToSchedule and pass them along, but this is inconvient. Making them global to indirect_scheduler, simplifies the code there
  # TODO: Check the forcePre
  if forcePre:
    sched.makeDAG_EnforceMode(userChoices)
  else:
    sched.makeDAG_RelaxMode(userChoices)

  # Alternative Approach
  #keyToNode, codeToKey, nodesToSchedule = makeDAG_EnforceMode(userChoices, db)

  # TODO: Make a class or file to wrap the pretty printing and output of the {{}} that is schedule
  schedule = sched.scheduleAll(minUnits, maxUnits, useSummer)

  printSched(schedule)

  #outputSchedule(schedule,params.outputPath)
  su.outputServerSchedule(schedule,params.outputPath)

# Start process
if __name__ == '__main__':
    main()
