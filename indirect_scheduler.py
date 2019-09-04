import string
import sched_utils as su
import os

# These are the key to implementing our system, rather than trying to pass them around all the time, we are just going to make them global.
# This can be changed
keyToNode = {}                # A DICT that matches a unique code with a Node/NodeGroup
codeToKey = {}                # A Lookup table that allows us to perform indirection (Multiple Course Codes -> Same Node)
nodesToSchedule = []          # List of keys, corresponding to the Nodes that we want to schedule
orKeyToStatus = {}            # DICT that maps the OR Relation to its status (Scheduled or Not Yet)

class NodeGroup:
  subNodes            = None        # {} course_code -> Node allows storing info about the components . NOTE: Just used as memory for when someone asks, but not for checks. NOTE: Can also contain other subNodes
  pre_reqs            = None        # See Node for details, same thing except this one is the set-wise union of all the subNodes list and the one we use for determining elgibility                                                           # NOTE: Don't know if we need this for a Group, as we can get it from our subNodes
  kids                = None        # The set-wise union of sub-node Kids, when we change, we have to tell them
  userSpecified       = None        # This tells us if this class was added as a pre-req or by the user
  schedule_me         = True        # All nodes start with this as True, it only gets set off if we hear back from a del_if
  key                 = None        # Each Node knows its unique ID or key

  # NOTE: For Co-Req OR, where the Co-Req inherits the OR of its lower Nodes, we may want a way to give predcedence to the single class, at this time this is a Future Feature TODO as we don't know of any such instances
  orRels             = None        # List of unique-keys that point to the or_relations that the Node is a part of. When the node is scheduled it must update the status at all of these relations. Additionally, when a Node's ready status is queried it needs to check the status of its relations. If any of its ORs are still unscheduled then it can still be scheduled

  keepAlive           = None        # This is the opposite of del_if, this tells us if someone needs us. If we are informed that person has been scheduled, then if we are not userSpecified and this list becomes empty schedule_me => False
  del_if              = None        # Includess the union of the subNodes del_ifs, but often is used for handling co-req or clusters, such that the cluster will have del_ifs not in the subNodes or even if the subNodes have no del_ifs     # Stores the keys to the other related Co-Or Clusters and the name of the primary associated course


  # Invoked by the Scheduler to get the list of classes in this block
  # Returns [ STR, STR, etc.] where STR is the Course Code for each of the SubNodes
  def getClasses(self):
    temp = []
    for key in self.subNodes:
      #print("SubNode:", key.getClasses())
      temp.extend(key.getClasses())
    return temp

  def getNumUnits(self):
    temp = 0
    for key in self.subNodes:
      temp += key.getNumUnits()
    return temp

  def getUnits(self, name):
    for key in self.subNodes:
      temp = key.getUnits(name)
      if temp != 0:
        return temp
    return 0

  def getTerms(self):
    temp = []
    for key in self.subNodes:
      if temp == []:
        temp.extend(key.getTerms())
      else:
        temp_2 = []
        for t in key.getTerms():
          if t in temp:
            temp_2.append(t)
        temp = temp_2

    return temp

  # Check that this term exists for all the subNodes
  def isOfferedIn(self, term):
    temp = True
    for key in self.subNodes:
      temp &= key.isOfferedIn(term)
    return temp

  # Check pre_reqs and del_if, remove from pre_reqs if heard, set schedule_me to false if in del_if
  def inform(self, names, key):
    for name in names:
      if name in self.pre_reqs:
        self.pre_reqs.remove(name)

      index = 0
      while len(self.pre_reqs) > 0 and index < len(self.pre_reqs):
        if isinstance(self.pre_reqs[index], list):
          if name in self.pre_reqs[index]:
            del self.pre_reqs[index]
            index -= 1
        index += 1

      if name in self.keepAlive:
        self.keepAlive.remove(name)
        if len(self.keepAlive) == 0 and not self.userSpecified:
          self.schedule_me = False

      if self.del_if != None and name in self.del_if:
        self.schedule_me = False
        # Consider if we want to delete from del_if

    if self.del_if != None and key in self.del_if:
      self.schedule_me = False
      # Consider if we want to delete from del_if

    # Would we want to propogate the death notice? -- Is removal from the toSchedule list due to another OR node the same as being scheduled?
    # Yes and No, If the kid shares a primary node, then yes, the delete should propogate, but if primary is different no
    # I believe that no, the scheduled node is responsiuble for informing all the other del_ifs, this should not recurse
    if not self.schedule_me:
      return self.key

    return None

  def informKids(self):
    global codeToKey, keyToNode, nodesToSchedule
    toRem = []
    for kid in self.kids:
      node = None
      if su.isInt(kid):
        node  = keyToNode[kid]
      else:
        key   = codeToKey[kid]
        node  = keyToNode[key]

      #print(self.getClasses())
      #print(self.key)

      res = node.inform(self.getClasses(), self.key)

      if res != None:
        toRem.append(res)

    for orKey in self.orRels:
      orKeyToStatus[orKey] = 1

    return toRem

  def readyToSchedule(self):
    allOrsSatisfied = False
    if self.orRels != [] and self.orRels != None:
      allOrsSatisfied = True
      for check in self.orRels:
        #print(check)
        #print(orKeyToStatus)
        if orKeyToStatus[check] != 1:
          allOrsSatisfied = False
          break

    """
    print()
    print(self.courseName)
    print("allOrsSatisfied = ", allOrsSatisfied)
    print("self.orRels = ", self.orRels)
    print("len(self.orRels) == 0) = ", len(self.orRels) == 0)
    print("self.userSpecified = ", self.userSpecified)
    print("self.schedule_me = ", self.schedule_me)
    print("len(self.pre_reqs) == 0  = ", len(self.pre_reqs) == 0 )
    print("( self.userSpecified or len(self.keepAlive) = ",  ( self.userSpecified or len(self.keepAlive) != 0 ) )
    print()
    """

    return ( (not allOrsSatisfied or ( self.orRels == None or len(self.orRels) == 0) ) or self.userSpecified ) and self.schedule_me and len(self.pre_reqs) == 0 and ( self.userSpecified or len(self.keepAlive) > 0 )

  def wantsToBeRemoved(self):
    return not self.schedule_me

  def getPreReqsForSetup(self):
    temp = []
    for key in self.subNodes:
      temp.extend(key.getPreReqsForSetup() )
    return temp

  def setupPreReqs(self):
    if self.pre_reqs == None:
      self.pre_reqs = []
    for key in self.subNodes:
      self.pre_reqs.extend( key.getPreReqsForSetup())

  def getKidsForSetup(self):
    temp = []
    for key in self.subNodes:
      temp.extend( key.getKidsForSetup() )
    return temp

  def setupKids(self):
    if self.kids == None:
      self.kids = []
    for key in self.subNodes:
      self.kids.extend( key.getKidsForSetup())

  def getOrLists_ForSetup(self):
    temp = []
    for key in self.subNodes:
      temp.extend( key.getOrLists_ForSetup() )
    return temp

  def setupOrRels(self):
    self.userSpecified = False
    if self.orRels == None:
      self.orRels = []

    for key in self.subNodes:
      self.userSpecified |= key.userSpecified
      self.orRels.extend( key.getOrLists_ForSetup())

  def get_Del_If_ForSetup(self):
    temp = []
    for key in self.subNodes:
      temp_2 = key.get_Del_If_ForSetup()
      if temp_2 != None:
        temp.extend( temp_2 )
    return temp

  def setupDel_Ifs(self):
    for key in self.subNodes:
      temp = key.get_Del_If_ForSetup()
      if self.del_if == None and temp != None and temp != []:
        self.del_if = []

      if self.del_if != None and temp != None:
        self.del_if.extend(temp)

  def get_KeepAlive_ForSetup(self):
    temp = []
    for key in self.subNodes:
      temp.extend( key.get_KeepAlive_ForSetup() )
    return temp

  def setupKeepAlive(self):
    self.userSpecified = False
    for key in self.subNodes:
      self.userSpecified |= key.userSpecified
      temp = key.get_KeepAlive_ForSetup()
      if self.keepAlive == None and temp != None and temp != []:
        self.keepAlive = []

      if self.keepAlive != None and temp != None:
        self.keepAlive.extend(temp)

  # Consider adding a parameter in the chain of getWeight and getWeightForParent() that also includes the call chain list, so that if we have a cycle we can still terminate
  def getWeightForParent(self, names, key):
    for name in names:
      if name in self.pre_reqs : #or ( self.del_if != None and name in self.del_if ):
        return self.getWeight()

    #if self.del_if != None and key in self.del_if:
    #  return self.getWeight()

    return 0

  def getWeight(self):
    weight = 0
    for key in self.subNodes:
      weight += key.getWeight()

    return weight


  """
  #Redundant Could just access the variable
  def getDelIf():
    return del_if

  def getKids():
    return pre_reqs

  def getPreReqs():
    return pre_reqs
  """

class Node:
  courseName          = None        # String that is my name
  numUnits            = None        # Int with the number of units for the course
  terms               = None        # Lists of Terms that the class is offered in
  pre_reqs            = None        # [ [STR, STR], STR ] , where sub-list indicates "OR" relation and the main list AND relation                                                                                       # Name            -- Relies on Course Being Scheduled not a specific Node
  kids                = None        # List of Listners, aka entities (Node or NodeGroup) that wants to be notified when I make a change (AM Scheculed or become a Group), id'd by either courseCode or keys             # Key or Name     -- Certain Classes need to know (For Pre-Req Reasons). Certain Hidden Nodes may also need to know (due to Co-Req Cluster)
  userSpecified       = None        # This tells us if this class was added as a pre-req or by the user
  schedule_me         = True        # All nodes start with this as True, it only gets set off if we hear back from a del_if
  key                 = None        # Each Node knows its unique ID or key, Key is set when the node is registered and a key is generated assigned when the

  # NOTE: For Co-Req OR, where the Co-Req inherits the OR of its lower Nodes, we may want a way to give predcedence to the single class, at this time this is a Future Feature TODO as we don't know of any such instances
  orRels             = None        # List of unique-keys that point to the or_relations that the Node is a part of. When the node is scheduled it must update the status at all of these relations. Additionally, when a Node's ready status is queried it needs to check the status of its relations. If any of its ORs are still unscheduled then it can still be scheduled

  del_if              = None        # Stores a list of names and keys that if we recieve inform from causes us to mark as no longer to be scheduled                                                                     # Key or Name     -- Probably could be only Name, but to be safe we allow both. This ensures that we can detect deletion more sensitively
  keepAlive           = None        # This is the opposite of del_if, this tells us if someone needs us. If we are informed that person has been scheduled, then if we are not userSpecified and this list becomes empty schedule_me => False
  # NOTE: About del_if : # Most often stays None, but otherwise has a list of keys to Nodes that if I recieve info have been scheduled will make request removal from the To Schedule list


  # Invoked by the Scheduler to get the list of classes in this block
  # Returns [ courseName ], this name and style is done to keep the interface to the scheduler the same as the Node Group
  def getClasses(self):
    return [ self.courseName ]

  def getNumUnits(self):
    return self.numUnits

  def getUnits(self, name):
    if name == self.courseName:
      return self.numUnits
    else:
      return 0

  def isOfferedIn(self, term):
    return term in self.terms

  def readyToSchedule(self):
    allOrsSatisfied = False
    if self.orRels != [] and self.orRels != None:
      allOrsSatisfied = True
      for check in self.orRels:
        #print(check , " :" , orKeyToStatus[check] )
        if orKeyToStatus[check] != 1:
          allOrsSatisfied = False
          break

    """
    print()
    print(self.courseName)
    print("allOrsSatisfied = ", allOrsSatisfied)
    print("self.orRels = ", self.orRels)
    print("len(self.orRels) == 0) = ", len(self.orRels) == 0)
    print("self.userSpecified = ", self.userSpecified)
    print("self.schedule_me = ", self.schedule_me)
    print("len(self.pre_reqs) == 0  = ", len(self.pre_reqs) == 0 )
    print("( self.userSpecified or len(self.keepAlive) = ",  ( self.userSpecified or len(self.keepAlive) != 0 ) )
    print()
    """

    return ( (not allOrsSatisfied or ( self.orRels == None or len(self.orRels) == 0) ) or self.userSpecified ) and self.schedule_me and len(self.pre_reqs) == 0 and ( self.userSpecified or len(self.keepAlive) > 0 )

  def wantsToBeRemoved(self):
    return not self.schedule_me

  def getPreReqsForSetup(self):
    return self.pre_reqs

  def getKidsForSetup(self):
    return self.kids

  def get_Del_If_ForSetup(self):
    return self.del_if

  # Not Really Needed
  def getKids(self):
    return self.kids

  def getPreReqs(self):
    return self.pre_reqs

  # Consider adding a parameter in the chain of getWeight and getWeightForParent() that also includes the call chain list, so that if we have a cycle we can still terminate
  def getWeightForParent(self, names, key):
    #print(self.courseName, " called by ", names, " or ", key)
    if isinstance(names, list):
      for name in names:
        for pre in self.pre_reqs:
          if isinstance(pre, list):
            if name in pre:
              #print("Returning Weights")
              return self.getWeight()
          elif name == pre:
            #print("Returning Weights")
            return self.getWeight()

        if self.del_if != None and name in self.del_if:
          #print("Returning Weights")
          return self.getWeight()
    else:
      for pre in self.pre_reqs:
        if isinstance(pre, list):
          if names in pre:
            #print("Returning Weights")
            return self.getWeight()
        elif names == pre:
          #print("Returning Weights")
          return self.getWeight()

    if self.del_if != None and key in self.del_if:
      #print("Returning Weights")
      return self.getWeight()

    #print("Returning 0")
    return 0

  # Basically iterate over kids passing the caller info and ask for weight, if callee has caller in their pre_req list or del_if list returns result of their getWeight() a Node with no pre_req returns 1. Note: THIS MUST BE A DAG (NO CYCLES) otherwise infinite loop or recusion stack overflow
  def getWeight(self):
    global codeToKey, keyToNode, nodesToSchedule
    weight = 1
    for kid in self.kids:
      node = None
      if su.isInt(kid):
        node  = keyToNode[kid]
      else:
        key   = codeToKey[kid]
        node  = keyToNode[key]

      weight += node.getWeightForParent(self.courseName, self.key)

    return weight

  def getTerms(self):
    return self.terms

  # Check pre_reqs and del_if, remove from pre_reqs if heard, set schedule_me to false if in del_if
  def inform(self, names, key):
    for name in names:
      if name in self.pre_reqs:
        self.pre_reqs.remove(name)

      index = 0
      while len(self.pre_reqs) > 0 and index < len(self.pre_reqs):
        if isinstance(self.pre_reqs[index], list):
          if name in self.pre_reqs[index]:
            del self.pre_reqs[index]
            index -= 1
        index += 1

      if name in self.keepAlive:
        self.keepAlive.remove(name)
        if len(self.keepAlive) == 0 and not self.userSpecified:
          self.schedule_me = False

      if self.del_if != None and name in self.del_if:
        self.schedule_me = False
        # Consider if we want to delete from del_if

    if self.del_if != None and key in self.del_if:
      self.schedule_me = False
      # Consider if we want to delete from del_if

    # Would we want to propogate the death notice? -- Is removal from the toSchedule list due to another OR node the same as being scheduled?
    # Yes and No, If the kid shares a primary node, then yes, the delete should propogate, but if primary is different no
    # I believe that no, the scheduled node is responsiuble for informing all the other del_ifs, this should not recurse
    if not self.schedule_me:
      return self.key

    return None

  def informKids(self):
    global codeToKey, keyToNode, nodesToSchedule
    toRem = []
    for kid in self.kids:
      node = None
      if su.isInt(kid):
        node  = keyToNode[kid]
      else:
        key   = codeToKey[kid]
        node  = keyToNode[key]

      #print(self.getClasses())
      #print(self.key)

      res = node.inform(self.getClasses(), self.key)

      if res != None:
        toRem.append(res)

    for orKey in self.orRels:
      print(self.courseName, " marking ", orKey, " satisfied ")
      orKeyToStatus[orKey] = 1

    return toRem

  def get_KeepAlive_ForSetup(self):
   return self.keepAlive

  def setup_KeepAlive(self):
   return self.keepAlive

  def getOrLists_ForSetup(self):
    return self.orRels

# Represents the Info about a scheduled Quarter
class Quarter:
  courseDict    = None  # Dict of Course Name  -> Num Units for the Courses scheduled this quarter
  curUnits      = 0     # Num of Units allocated to this quarter
  term          = None  # A single term indicating Autumn, Winter, Spring, Summer
  year          = None  # The Year of the Quarter

  def __init__(self, trm, yr):
    self.courseDict    = {}
    self.curUnits      = 0
    self.term          = trm
    self.year          = yr


  def add(self, node):
    # Append the Main Class
    classes = node.getClasses()
    unit_sum = 0
    for c in classes:
      # TODO: Check if the unit number returned is 0, as this indicates that their was no node in the course with that name, which would be very bad and should never happen
      self.courseDict[c] = node.getUnits(c)
      unit_sum += node.getUnits(c)

    # Update the number of units to account for main and co-reqs
    # Since we already added up the sub units, may as well not reinvoke the wheel
    self.curUnits += unit_sum
    #curUnits += node.getTotalUnits()

  def output(self):
    for key in self.courseDict:
      print(key)

  def hasClasses(self):
    return len(self.courseDict.keys()) > 0

# Assumes that this is just an existence check not a sophisticated check that considers if already scheduled
def hasReqs(reqs):
  return len(reqs[0]) > 0 or len(reqs[1]) > 0 or len(reqs[2]) > 0

# Ensures that the next insertion has a unique intermediary key
newKey = 0
def addKeyNodePair(newNode):
  global codeToKey, keyToNode, nodesToSchedule
  global newKey
  keyToNode[newKey] = newNode
  keyToNode[newKey].key = newKey
  newKey += 1

  return newKey - 1

# Make an entry for the courseCode
def registerNode(courseCode, node):
  global codeToKey, keyToNode, nodesToSchedule
  key = addKeyNodePair(node)
  codeToKey[courseCode] = key

  # Assuming that when any node is registered it now wants to be considered for scheduling
  nodesToSchedule.append(key)

# If a node doesn't exit it will create it and have it begin recursive DAG construction
# Gurantees that on exist the node is real and exists
def makePreReqNode(spName, childCode, childKey, courseDict, or_key = None):
  global codeToKey, keyToNode, nodesToSchedule
  # This check may be our current defence against cycles (Should they occur)
  # It is originally placed as we don't have deterministic order generation
  if spName not in codeToKey:
    # Initialize the New Node
    spNode = Node()
    spNode.courseName = spName
    spNode.pre_reqs   = []
    spNode.kids       = []
    spNode.keepAlive  = [childCode]
    spNode.userSpecified = False

    spNode.orRels = []
    if or_key != None:
      spNode.orRels.append(or_key)

    # Add ourselves to the list of listeners
    spNode.kids.extend([childKey, childCode])

    # Lookup info for this node
    spReqs, spTerms, spUnits = lookup(spName)

    # Further populate the node
    spNode.terms = spTerms
    if spName in courseDict:
      spNode.numUnits   = courseDict[spName]
      spNode.userSpecified = True
    else:
      spNode.numUnits   = spUnits

    # Register/Insert the Node into our system
    registerNode(spName, spNode)

    processReqs(spNode, spName, spReqs, courseDict)
  # If the Node already exists, please inform it that we want to know about what happens to it
  else:
    key = codeToKey[spName]
    keyToNode[key].kids.extend( [childKey, childCode] )

    # Any one who has us in there pre-req chain is relying on us
    if isinstance(childCode, list):
      keyToNode[key].keepAlive.extend( childCode )
    else:
      keyToNode[key].keepAlive.append( childCode )

    if or_key != None:
      if keyToNode[key].orRels == None:
        keyToNode[key].orRels = []
      keyToNode[key].orRels.append(or_key)

# Assumes that both nodes exist and are setup correctly
def merge(curNode, coName, or_key = None):
  global codeToKey, keyToNode, nodesToSchedule
  curKey = curNode.key

  newNodeGroup = NodeGroup()
  newNodeGroup.subNodes = []
  newNodeGroup.subNodes.append(curNode)

  # Retrieve the second node
  key = None
  if su.isInt(coName):
    key = coName
    node = keyToNode[coName]
  else:
    key  = codeToKey[coName]
    node = keyToNode[key]

  newNodeGroup.subNodes.append(node)

  if or_key != None:
    newNodeGroup.orRels = []
    newNodeGroup.orRels.append(or_key)

  # Automatically populates the list field for the Group Node
  newNodeGroup.setupPreReqs()
  newNodeGroup.setupKids()
  newNodeGroup.setupDel_Ifs()
  newNodeGroup.setupKeepAlive()
  newNodeGroup.setupOrRels()

  # Node now initialized

  # Register/Insert the CoNode
  newKey = addKeyNodePair(newNodeGroup)

  # Update the indirection list
  names = newNodeGroup.getClasses()
  for name in names:
    codeToKey[name] = newKey

  # Assuming that when any node is registered it now wants to be considered for scheduling
  nodesToSchedule.append(newKey)

  # Delete the prior Nodes from ToSchedule if present
  if curKey in nodesToSchedule:
    nodesToSchedule.remove(curKey)

  if key in nodesToSchedule:
    nodesToSchedule.remove(key)

  return newKey


def registerOrKey(courseName, or_count):
  # Register the OR
  key = courseName + "_" + str(or_count)
  orKeyToStatus[key] = 0
  or_count += 1

  #print("Registerd: ", key)

  return key, or_count

# PreReq-Eval will be recursive
# TODO: Consider making it non-recursive
# Basically Tree/DAG Traversal
# No Return, all relevant created nodes are auto-inserted
def processReqs(curNode, courseCode, reqs, courseDict):
  global codeToKey, keyToNode, nodesToSchedule
  if hasReqs(reqs):
    or_count = 0
    callerKey = codeToKey[courseCode]
    # If there are pre-reqs, handle the pre-reqs:
    # NOTE: We plan to handle Soft-Co-Req just as pres, so we may want to merge reqs[0] and reqs[2]
    # --------------------------------- Handling Soft as Pre by Merge -----------------------------

    combinedReqs = []
    combinedReqs.extend(reqs[0])
    combinedReqs.extend(reqs[2])

    # --------------------------------- Merge Complete     ----------------------------------------
    #for pre in reqs[0]:
    for pre in combinedReqs:
      if "|" in pre:
        print("Handling an OR PRE")
        or_list = []

        or_key, or_count = registerOrKey(courseCode, or_count)

        for sp in pre.split("|"):
          # We could check if we need to do this before doing, but for we just do it always
          # Course Code Lookup Expects Exactly 1 Space, so we remove then add
          # In the future, we could verify that this is already true in the database and eliminate the sanitization completely
          spName = su.addSpace(sp.translate(str.maketrans('','',string.whitespace)))
          or_list.append(spName)

          # No return, because we don't care about the node, just that it exists
          makePreReqNode(spName, courseCode, callerKey, courseDict, or_key)

        # Now that we have successfully generated each of our "parent" dependencies for the OR relation, add the relation to our list
        curNode.pre_reqs.append(or_list)

        # For Ours, once one of them is scheduled, then there is no one else potentially needing the other class, so to avoid scheduling it, we need to notify it
        # Thus it becomes a dependant or kid of curNode
        curNode.kids.append(spName)

      else:
        preName = su.addSpace(pre.translate(str.maketrans('','',string.whitespace)))

        # No return, because we don't care about the node, just that it exists
        makePreReqNode(preName, courseCode, callerKey, courseDict)

        # We are guranteed that our parent exists somewhere now.
        curNode.pre_reqs.append(preName)

    # Handle the Co-Reqs
    # NOTE: We are not supporting Co-Req clumping at this time or at least not in this pass/merge op
    if len(reqs[1]) > 0:
      curKey = codeToKey[courseCode]
      list_of_or_lists = []
      for co in reqs[1]:
        if "|" in co:
          print("Handling an OR CO-Req")
          or_list = []
          #print(co.split("|"))
          for coName in co.split("|"):
            # Starts off the same as a normal co/pre req we need to create each of the or nodes
            cName = su.addSpace(coName.translate(str.maketrans('','',string.whitespace)))
            #print(cName)
            makePreReqNode(cName, courseCode, callerKey, courseDict)
            or_list.append(cName)

          # At this point, we safely know that the current node, and its OR Co-Reqs are in existence
          # However, we do not know if any additional and co-reqs are resolved or will be resolved so, we punt until
          list_of_or_lists.append(or_list)

        else:
          # Need to ensure that the other exists before we can perform merge
          coName = su.addSpace(co.translate(str.maketrans('','',string.whitespace)))
          makePreReqNode(coName, courseCode, callerKey, courseDict)

          originalCurKey = curKey
          coKey = codeToKey[coName]

          # Setup the mega node and set our current Node Key pointer to the new mega node
          curKey = merge(keyToNode[curKey], coName)

          # Remove these nodes from the toSchedule List
          #nodesToSchedule.remove(originalCurKey)
          #nodesToSchedule.remove(coKey)


      # At this point all AND co-reqs have been resolved and OR relation co-reqs brought into existence.
      # Our goal is now to perform the OR Co-Req clustering, while treating the current NODE (made up of the ANDS) as the primary that will be in both/all ORs
      # This approach may or may not work when their are multiple or_lists
      # It should work if we track the intermediaries created after each or-list is resolved and use those as parent seed to the next

      listOfSeedKeys = [curKey]
      for or_list in list_of_or_lists:
        newNodesKeys = []
        # Create All of the unique OR Tuples using listOfSeedKeys by or_list
        # Remove the original listOfSeedKeys and OR Tuples classes from ToSchedule
        # Add each of the new nodes to ToSchedule
        # Record the new keys as our new list ofSeedKeys
        for o in or_list:
          coNodeKey = codeToKey[o]
          or_key, or_count = registerOrKey(courseCode, or_count)
          for seed in listOfSeedKeys:
            #print(seed, coNodeKey)
            #print(codeToKey)
            #print(keyToNode)
            newNodesKeys.append(merge( keyToNode[seed], coNodeKey, or_key) )

        # Setup the del_if relationship
        for newNodeKey in newNodesKeys:
          for otherNodeKey in newNodesKeys:
            newNode   = keyToNode[newNodeKey]
            otherNode = keyToNode[otherNodeKey]
            if newNode.key != otherNode.key:
              # If the current class is scheduled ever, then these other nodes all die
              # We make these nodes sensitive to one another by making them dependants of one another on both the current class and the other node keys.
              # NOTE: This means if I am already no longer going to be scheduled, I shouldn't propogate that piece of info after the 1st time
              if newNode.del_if == None:
                newNode.del_if = []
              newNode.del_if.extend( [ newNode.key, courseCode ] )
              otherNode.kids.extend( [ newNode.key, courseCode ] )

        # For the next or_list we seed with the current OR population as AND of 2 ORs means that 1 true from both lists gratifies.
        # We believe this is the correct implementation, but probably will never have this case invoked, but it is here in case
        # TODO/FUTURE WORK: Validate this
        listOfSeedKeys = newNodesKeys.copy()

  # The New curNode, may not be the same after CoReq resolution
  #return curNode

# Making the DB global so lookup can get to it and we don't need to pass it around
db = {}
def loadDB(dbPath):
  fileDir = os.path.dirname(os.path.realpath('__file__'))
  filename = os.path.join(fileDir, './' + dbPath)
  inFile = open(filename, "r")
  for line in inFile:
    data = line.strip().split( ">" )
    # Key > Max Units > Term, Term > Pre ; Co ; Sup

    units = int(data[1].strip())
    terms = []
    for term in data[2].strip().split(","):
      if term.strip() != "":
        terms.append(term.strip().upper())

    if len(terms) == 0:
      #print(terms)
      # If no info about offerings, just assume all viable
      terms = ["AUTUMN", "WINTER", "SPRING"]

    # Debug Check
    #if len(terms) == 1:
    #  if terms[0] not in ["AUTUMN", "WINTER", "SPRING", "SUMMER"]:
    #    print(terms[0])


    reqs = []
    for sec in data[3].strip().split(";"):
      reqs.append([])
      if sec.strip() != "":
        for c in sec.strip().split(","):
          reqs[-1].append(c)

    if len(reqs) == 2:
      reqs.append([])
    elif len(reqs) != 3:
      print("Error: Misparse on reqs!!")
      quit()

    # Create the entry with the info
    db[data[0].strip()] = (reqs, terms, units)

  inFile.close()
  #return db


def lookup(name):
  print(name, ":", db[name])
  tup = db[name]
  return tup[0], tup[1], tup[2]

# courseDict is the parsed version of the input of the user selection
# Assumes:
#     Course Aliases have been de-duplicated    # NOTE: Probably a future feature, but not an obstacle to operation
#     Course Codes have one seperation space
#     All Courses in the list are real/exist in the database
#     All courses are only to be taken once, unless they are secondary co-req. AKA No repeat Courses
#       -- This last assumption can be removed, but will need to chang:
#             How we remove from nodesToSchedule
#             Potentially the Del-If structure
#
# Builds the Schedule DAG
def makeDAG_EnforceMode(courseDict):
  # Not sure if we need a .copy(), can try without later, better safe now
  userCourses = list(courseDict.keys()) #.deepcopy()

  while len(userCourses) > 0:
    print("Processing: ", userCourses [0] )
    curCourseName = userCourses [0]
    if curCourseName not in codeToKey:
      curNode       = Node()

      # TODO: Write this and integrate the database
      reqs, terms, units = lookup(curCourseName)

      curNode.courseName    = curCourseName
      curNode.numUnits      = courseDict[curCourseName]
      curNode.terms         = terms
      curNode.kids          = []
      curNode.pre_reqs      = []
      curNode.keepAlive     = []
      curNode.orRels        = []
      curNode.userSpecified = True

      registerNode(curCourseName, curNode)

      if hasReqs(reqs):
        processReqs(curNode, curCourseName, reqs, courseDict)

    del userCourses [0]

# This will remove target and promote it's unparented(now completely parent-free) children to root nodes or delete nodes that no longer want to be scheduled
# Basically this goes through the kids list and invokes inform on all the kids with the key and course code of the caller
def updateRoots(nodesToSchedule, target):
  # Removes target from list and informs it's kids.
  # After Inform of the kids, we also query them to see if any want to be killed
  # NOTE: There is currently no longer a notion of a root list, all nodes are in nodesToSchedule and ready nodes are detected by readyToSchedule()
  # This means that only ndoes that want to be removed need to be queried

  # Create a list with the keys for the nodes that want to be removed from the toSchedule List
  nodesToDel = []
  node = keyToNode[target]
  nodesToDel.extend( node.informKids() )

  for key in nodesToDel:
    if key in nodesToSchedule:
      nodesToSchedule.remove(key)

# Gets the Highest Weight Node
def findNextNode(nodeList, minUnits, maxUnits, quarter):
  print("\ncurrent Term =", quarter.term)
  global codeToKey, keyToNode, nodesToSchedule
  highestWeight = 0
  chosen = None
  for nodeKey in nodeList:
    node = keyToNode[nodeKey]
    weight = node.getWeight()
    print(node.getClasses(), " has weight :" , weight, " ready = ", str(node.readyToSchedule()), " has ", node.getNumUnits(), "units and is avl in", node.getTerms(), "orRels =", node.orRels, "pre_reqs =", node.pre_reqs, "kids =", node.kids, "keep_alive =", node.keepAlive, "del_if =", node.del_if)
    # TODO: Add an emphasis or bias for classes with the same Co-Req to be scheduled in the same quarter by giving them higher weights if co-req already assigned or implement clumping
    if weight > highestWeight and node.isOfferedIn(quarter.term) and node.readyToSchedule() and ( (node.getNumUnits() + quarter.curUnits) <= maxUnits ) :
      highestWeight = weight
      chosen = nodeKey

  if chosen != None:
    print("Chose:" , keyToNode[chosen].getClasses(), "\n")
  else:
    print("Chose:", chosen, "\n")
  return chosen #, highestWeight

def updateOrRels( target ):
  node = keyToNode[target]

  if node.orRels != None:
    for or_rel in node.orRels:
      orKeyToStatus[or_rel] = 1


# Schedule from the Tree
# TODO: Run MinUnits as eval at the end and identify as quarters for fun filler classess
def schedule_quarter(minUnits, maxUnits, quarter):
  global codeToKey, keyToNode, nodesToSchedule
  scheduledNodes = []
  while len(nodesToSchedule) > 0:
    target = findNextNode(nodesToSchedule, minUnits, maxUnits, quarter)

    # If we can no longer schedule classes in this quarter exit
    if target == None:
      break
    quarter.add( keyToNode[target]  )
    scheduledNodes.append(target)
    nodesToSchedule.remove(target)
    # TODO: Add a special inform in the loop just for deletition to make sure OR Coreqs don't accidently schedule in the same quarter
    updateOrRels(target)

  # Needs to be outside the loop so class that become eligible are not scheduled in the same quarter
  # Update the nodesToSchedule list and the other nodes based on the insertion
  for target in scheduledNodes:
    updateRoots(nodesToSchedule, target)

# We still need another fucntion before this that build the tree and enumerates the root nodes from the json collected by the UI
def scheduleAll(minUnits, maxUnits, summerAllowed):
  # Goal/Termination Conditions:
  #   1) Schedule all classes -- This is the ideal
  #   2) Error State - Unable to schedule any new classes for 1 year
  # High-Level, if you can't schedule anything for a year and you still have class report error
  global codeToKey, keyToNode, nodesToSchedule
  classes_scheduled_in_past_year = True       # Allows do while behaviou
  seed_year  = 2018             # Decide if this is 0, 1, or like 2020, etc.
  year_count = 0
  schedule = {}       #Schedule()
  termOptions = ["AUTUMN", "WINTER", "SPRING"]
  if summerAllowed:
    termOptions.append("SUMMER")
  while classes_scheduled_in_past_year == True and len(nodesToSchedule) > 0 :
    year = str(seed_year + year_count) + "-" + str(seed_year + 1 + year_count)
    classes_scheduled_in_past_year = False
    schedule[year] = {}
    for term in termOptions:
      schedule[year][term] = Quarter(term, year)
      schedule_quarter(minUnits, maxUnits, schedule[year][term])

      # Only need to update if we didn't know something had been scheduled and something has now been scheduled
      if not classes_scheduled_in_past_year and schedule[year][term].hasClasses():
        classes_scheduled_in_past_year = True

    year_count  += 1

  if len(nodesToSchedule) > 0:
    print("Error Couldn't Schedule all Nodes!!!")
    for node in nodesToSchedule:
      print(keyToNode[node].getClasses())
    print("\n\n\n\n")

  return schedule

"""
def ascii_encode_dict(data):
    ascii_encode = lambda x: x.encode('ascii')
    return dict(map(ascii_encode, pair) for pair in data.items())

json.loads(json_data, object_hook=ascii_encode_dict)
"""

import json
def jsonToCourseList(jsonFilePath):
  fileDir = os.path.dirname(os.path.realpath('__file__'))
  filename = os.path.join(fileDir, './' + jsonFilePath)
  webInput = json.load( open(filename, "r"), encoding="ascii" )
  courseList = {}
  for elm in webInput [ "courses" ]:
    courseList[ elm["code"] ] = elm["units"]

  return courseList, webInput["maxUnitsPerQuarter"], webInput["minUnitsPerQuarter"], webInput["scheduleInSummer"], webInput["considerPrereqs"]

def pruneUserChoices(userChoices):
  index = 0
  while index < len(userChoices.keys()) and len(userChoices) != 0:
    key = sorted(userChoices.keys()) [index]
    if key.strip() not in db:
      print("'", key, "' not in DB and thus cannot be processed")
      del userChoices[key]
      index -= 1
    index += 1

  return userChoices

# ------------------------------------------------- No force section -----------------------------------------------------------


def makePreReqNodeRelax(spName, childCode, childKey, courseDict, or_key = None):
  global codeToKey, keyToNode, nodesToSchedule
  # This check may be our current defence against cycles (Should they occur)
  # It is originally placed as we don't have deterministic order generation
  if spName not in codeToKey:
    # Initialize the New Node
    spNode = Node()
    spNode.courseName = spName
    spNode.pre_reqs   = []
    spNode.kids       = []
    spNode.keepAlive  = [childCode]
    spNode.userSpecified = False

    spNode.orRels = []
    if or_key != None:
      spNode.orRels.append(or_key)

    # Add ourselves to the list of listeners
    spNode.kids.extend([childKey, childCode])

    # Lookup info for this node
    spReqs, spTerms, spUnits = lookup(spName)

    # Further populate the node
    spNode.terms = spTerms
    if spName in courseDict:
      spNode.numUnits   = courseDict[spName]
      spNode.userSpecified = True
    else:
      spNode.numUnits   = spUnits

    # Register/Insert the Node into our system
    registerNode(spName, spNode)

    processReqsRelax(spNode, spName, spReqs, courseDict)
  # If the Node already exists, please inform it that we want to know about what happens to it
  else:
    key = codeToKey[spName]
    keyToNode[key].kids.extend( [childKey, childCode] )

    # Any one who has us in there pre-req chain is relying on us
    if isinstance(childCode, list):
      keyToNode[key].keepAlive.extend( childCode )
    else:
      keyToNode[key].keepAlive.append( childCode )

    if or_key != None:
      if keyToNode[key].orRels == None:
        keyToNode[key].orRels = []
      keyToNode[key].orRels.append(or_key)

def pruneReqsForRelax(reqs, courseDict):
  newReqs = []
  index = 0
  for cat in reqs:
    newReqs.append([])
    for req in cat:
      if "|" in req:
        valid = []
        for name in req.split("|"):
          spName = su.addSpace(name.translate(str.maketrans('','',string.whitespace)))
          if spName in courseDict:
            valid.append(spName)

        if valid != []:
          serialize = ""
          for entry in valid:
            if serialize != "":
              serialize += "|"
            serialize += entry

        newReqs[index].append(serialize)
      elif req in courseDict:
        newReqs[index].append(req)
    index += 1

  return newReqs


def processReqsRelax(curNode, courseCode, reqs, courseDict):
  global codeToKey, keyToNode, nodesToSchedule

  reqs = pruneReqsForRelax(reqs, courseDict)

  if hasReqs(reqs):
    or_count = 0
    callerKey = codeToKey[courseCode]
    # If there are pre-reqs, handle the pre-reqs:
    # NOTE: We plan to handle Soft-Co-Req just as pres, so we may want to merge reqs[0] and reqs[2]
    # --------------------------------- Handling Soft as Pre by Merge -----------------------------

    combinedReqs = []
    combinedReqs.extend(reqs[0])
    combinedReqs.extend(reqs[2])

    # --------------------------------- Merge Complete     ----------------------------------------
    #for pre in reqs[0]:
    for pre in combinedReqs:
      if "|" in pre:
        print("Handling an OR PRE")
        or_list = []

        or_key, or_count = registerOrKey(courseCode, or_count)

        for sp in pre.split("|"):
          # We could check if we need to do this before doing, but for we just do it always
          # Course Code Lookup Expects Exactly 1 Space, so we remove then add
          # In the future, we could verify that this is already true in the database and eliminate the sanitization completely
          spName = su.addSpace(sp.translate(str.maketrans('','',string.whitespace)))
          or_list.append(spName)

          # No return, because we don't care about the node, just that it exists
          makePreReqNodeRelax(spName, courseCode, callerKey, courseDict, or_key)

        # Now that we have successfully generated each of our "parent" dependencies for the OR relation, add the relation to our list
        curNode.pre_reqs.append(or_list)

        # For Ours, once one of them is scheduled, then there is no one else potentially needing the other class, so to avoid scheduling it, we need to notify it
        # Thus it becomes a dependant or kid of curNode
        curNode.kids.append(spName)

      else:
        preName = su.addSpace(pre.translate(str.maketrans('','',string.whitespace)))

        # No return, because we don't care about the node, just that it exists
        makePreReqNodeRelax(preName, courseCode, callerKey, courseDict)

        # We are guranteed that our parent exists somewhere now.
        curNode.pre_reqs.append(preName)

    # Handle the Co-Reqs
    # NOTE: We are not supporting Co-Req clumping at this time or at least not in this pass/merge op
    if len(reqs[1]) > 0:
      curKey = codeToKey[courseCode]
      list_of_or_lists = []
      for co in reqs[1]:
        if "|" in co:
          print("Handling an OR CO-Req")
          or_list = []
          #print(co.split("|"))
          for coName in co.split("|"):
            # Starts off the same as a normal co/pre req we need to create each of the or nodes
            cName = su.addSpace(coName.translate(str.maketrans('','',string.whitespace)))
            #print(cName)
            makePreReqNodeRelax(cName, courseCode, callerKey, courseDict)
            or_list.append(cName)

          # At this point, we safely know that the current node, and its OR Co-Reqs are in existence
          # However, we do not know if any additional and co-reqs are resolved or will be resolved so, we punt until
          list_of_or_lists.append(or_list)

        else:
          # Need to ensure that the other exists before we can perform merge
          coName = su.addSpace(co.translate(str.maketrans('','',string.whitespace)))
          makePreReqNodeRelax(coName, courseCode, callerKey, courseDict)

          originalCurKey = curKey
          coKey = codeToKey[coName]

          # Setup the mega node and set our current Node Key pointer to the new mega node
          curKey = merge(keyToNode[curKey], coName)

          # Remove these nodes from the toSchedule List
          #nodesToSchedule.remove(originalCurKey)
          #nodesToSchedule.remove(coKey)


      # At this point all AND co-reqs have been resolved and OR relation co-reqs brought into existence.
      # Our goal is now to perform the OR Co-Req clustering, while treating the current NODE (made up of the ANDS) as the primary that will be in both/all ORs
      # This approach may or may not work when their are multiple or_lists
      # It should work if we track the intermediaries created after each or-list is resolved and use those as parent seed to the next

      listOfSeedKeys = [curKey]
      for or_list in list_of_or_lists:
        newNodesKeys = []
        # Create All of the unique OR Tuples using listOfSeedKeys by or_list
        # Remove the original listOfSeedKeys and OR Tuples classes from ToSchedule
        # Add each of the new nodes to ToSchedule
        # Record the new keys as our new list ofSeedKeys
        for o in or_list:
          coNodeKey = codeToKey[o]
          or_key, or_count = registerOrKey(courseCode, or_count)
          for seed in listOfSeedKeys:
            #print(seed, coNodeKey)
            #print(codeToKey)
            #print(keyToNode)
            newNodesKeys.append(merge( keyToNode[seed], coNodeKey, or_key) )

        # Setup the del_if relationship
        for newNodeKey in newNodesKeys:
          for otherNodeKey in newNodesKeys:
            newNode   = keyToNode[newNodeKey]
            otherNode = keyToNode[otherNodeKey]
            if newNode.key != otherNode.key:
              # If the current class is scheduled ever, then these other nodes all die
              # We make these nodes sensitive to one another by making them dependants of one another on both the current class and the other node keys.
              # NOTE: This means if I am already no longer going to be scheduled, I shouldn't propogate that piece of info after the 1st time
              if newNode.del_if == None:
                newNode.del_if = []
              newNode.del_if.extend( [ newNode.key, courseCode ] )
              otherNode.kids.extend( [ newNode.key, courseCode ] )

        # For the next or_list we seed with the current OR population as AND of 2 ORs means that 1 true from both lists gratifies.
        # We believe this is the correct implementation, but probably will never have this case invoked, but it is here in case
        # TODO/FUTURE WORK: Validate this
        listOfSeedKeys = newNodesKeys.copy()

  # The New curNode, may not be the same after CoReq resolution
  #return curNode


def makeDAG_RelaxMode(courseDict):
  # Not sure if we need a .copy(), can try without later, better safe now
  userCourses = list(courseDict.keys()) #.deepcopy()

  while len(userCourses) > 0:
    print("Procesing: ", userCourses [0] )
    curCourseName = userCourses [0]
    if curCourseName not in codeToKey:
      curNode       = Node()

      # TODO: Write this and integrate the database
      reqs, terms, units = lookup(curCourseName)

      curNode.courseName    = curCourseName
      curNode.numUnits      = courseDict[curCourseName]
      curNode.terms         = terms
      curNode.kids          = []
      curNode.pre_reqs      = []
      curNode.keepAlive     = []
      curNode.orRels        = []
      curNode.userSpecified = True

      registerNode(curCourseName, curNode)

      if hasReqs(reqs):
        processReqsRelax(curNode, curCourseName, reqs, courseDict)

    del userCourses [0]
