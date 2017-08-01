from cloud import *
import time


class Operator:
    def __init__(self, operator):
        self.operator = operator

    def process(self, left, right):
        print "Processing: "
        print left
        print self.operator
        print right
        print (self.operator == 'Greater than')
        print (float(left) > float(right)
        if (self.operator == 'Greater than'):
            return left > right
        elif (self.operator == "Less than"):
            return left < right
        elif (self.operator == "Less than or equal to"):
            return left <= right
        elif (self.operator == "Greater than or equal to"):
            return left >= right
        elif (self.operator == "Equals"):
            return left == right
        elif (self.operator == "Not equal to"):
            return left != right
        elif (self.operator == "AND"):
            return left and right
        elif (self.operator == "OR"):
            return left or right
        else:
            return False


class Action:
    def __init__(self, actuator_name, value, cloud):
        self.actuator_name = actuator_name
        self.value = value
        self.cloud = cloud

    def execute(self):
        data = self.cloud.getDataFromCache(self.actuator_name)
        if(data is not None):
            data['data']['status'] = self.value
        self.cloud.publish(data)


class Condition:
    def __init__(self):
        self.dirty = False

    def isDirty(self):
        return self.dirty

    def setDirty(self, value):
        self.dirty = value

    def evaluate(self):
        return False


class ConstCondition(Condition):
    def __init__(self, value):
        Condition.__init__(self)
        self.constant = value

    def evaluate(self):
        return self.constant


class LeftRightCondition(Condition):
    def __init__(self, left, op, right):
        Condition.__init__(self)
        self.left = left
        self.right = right
        self.op = op

    def isDirty(self):
        return self.left.isDirty() or self.right.isDirty()

    def setDirty(self, value):
        self.left.setDirty(value)
        self.right.setDirty(value)

    def evaluate(self):
        result =  self.op.process(self.left.evaluate(), self.right.evaluate())
        print "LeftRightCondition evaluated: "
        print result
        return result


class CloudCondition(Condition):
    def __init__(self, channel_name, cloud):
        Condition.__init__(self)
        self.cloud = cloud
        self.channel_name = channel_name
        self.name = channel_name + "_monitor"
        self.value = None
        # Get the last stored value for this channel if there is one
        data = cloud.getDataFromCache(channel_name)
        print "Cloud Condition init:"
        print data
        if (data is not None) and ('data' in data) and ('status' in data['data']):
            self.value = data['data']['status']
        # Subscribe to the channel to get updates from it
        cloud.subscribe(self, channel_name)

    def evaluate(self):
        return self.value

    def on_update(self, data):
        value = self.value
        if(data is not None) and ('data' in data) and ('status' in data['data']):
            value = data['data']['status']

        if(value != self.value):
            self.value = value
            self.dirty = True
        else:
            self.dirty = False


class GroupCondition(Condition):
    def __init__(self, conditions, op):
        Condition.__init__(self)
        self.conditions = conditions
        self.op = op

    def isDirty(self):
        self.dirty = False
        for condition in self.conditions:
            self.dirty = self.dirty or condition.isDirty()
        return self.dirty
    
    def setDirty(self, value):
        for condition in self.conditions:
            condition.setDirty(value)

    def evaluate(self):
        result = self.conditions[0].evaluate()
        for condition in self.conditions:
            result = self.op.process(result, condition.evaluate())
        return result


class Rule:
    def __init__(self, name, cloud):
        self.cloud = cloud
        self.name = name
        cloud.subscribe(self, name)

    def parseCondition(self, c):
        #determine what type of condition this is...
        if( 'constant' in c ):
            return ConstCondition(c['constant'])
        elif('left' in c) and ('right' in c) and ('op' in c):
            left = self.parseCondition(c['left'])
            right = self.parseCondition(c['right'])
            op = Operator(c['op'])
            return LeftRightCondition(left, op, right)
        elif( 'channel_name' in c ):
            return CloudCondition(c['channel_name'], self.cloud)
        elif( 'conditions' in c and 'op' in c):
            if (len(c['conditions']) > 1):
                conditions = []
                for condition in c['conditions']:
                    conditions.append(self.parseCondition(condition))
                return GroupCondition(conditions, Operator(c['op']))
            elif (len(c['conditions']) == 1):
                return self.parseCondition(c['conditions'][0])
            else:
                return None
        elif( 'sensor' in c and 'op' in c and 'value' in c):
            return LeftRightCondition( CloudCondition(c['sensor'], self.cloud), Operator(c['op']), ConstCondition(c['value']))
        else:
            return None

    def parseActions(self, data):
        if(data is None):
            return None
        actions = []
        for a in data:
            if('actuator' in a) and ('value' in a):
                actions.append(Action(a['actuator'], a['value'], self.cloud))
        
        return actions

    def on_update(self, data):
        if VERBOSE:
            print('%s got update:' % self.name)
            print data
        if( data is None ):
            return
        if( 'condition' in data ):
            self.condition = self.parseCondition(data['condition'])
        if( 'actions' in data ):
            self.actions = self.parseActions(data['actions']) 
    
    def evaluate(self):
        if(self.condition.isDirty()):
            self.condition.setDirty(False)
            if(self.condition.evaluate() is True):
                if VERBOSE:
                    print "Determined that rule " + self.rule + " was met. Executing actions..."
                for action in self.actions:
                    action.execute()
        
class RulesManager:
    def __init__(self, name, cloud, pulled_data):
        self.cloud = cloud
        self.name = name
        self.thread = threading.Thread(target = self.rulesThread)
        self.thread.daemon = True
        self.rules = {}
        # Search pulled data for any existing rules and add them to the rules dictionary
        if(pulled_data is not None):
            matches = (entry for entry in pulled_data if (('channel_type' in entry) and (entry['channel_type']=="rule")))
            for match in matches:
                name = match['channel_name']
                self.rules[name] = Rule(name,cloud)
                self.rules[name].on_update(match)
        # Subscribe to the rules manager channel for rule management updates
        cloud.subscribe(self, name)
    
    def on_update(self, data):
        if VERBOSE:
            print('%s got update:' % self.name)
            print data
        if (data is None) or ('rules' not in data):
            return
        # There can be multiple entries 
        for entry in data['rules']:
            if('name' in entry) and ('action' in entry):
                if (entry['action'] == "delete") and (entry['name'] in self.rules):
                    del self.rules[entry['name']]
                    if VERBOSE:
                        print "Deleted rule ["+ entry['name'] +"] from rules manager"
                elif (entry['action'] == "add") and (entry['name'] not in self.rules):
                    self.rules[entry['name']] = Rule(entry['name'], self.cloud)
                    if VERBOSE:
                        print "Added rule [" + entry['name'] + "] to rules manager"
                    if('rule' in entry):
                        self.rules[entry['name']].on_update(entry['rule'])
    
    def start(self):
        self.thread.start()

    def rulesThread(self):
        while True:
            for rule in self.rules:
                self.rules[rule].evaluate()
            time.sleep(0.5)
