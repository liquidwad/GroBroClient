from cloud import *

class Operator:
    def __init__(self, operator):
        self.operator = operator
    
    def process(self, left, right):
        if(self.operator == ">"):
            return left > right
        elif(self.operator == "<"):
            return left < right
        elif(self.operator == "<="):
            return left <= right
        elif(self.operator == ">="):
            return left >= right
        elif(self.operator == "=="):
            return left == right
        elif(self.operator == "!="):
            return left != right
        elif(self.operator == "&&"):
            return left and right
        elif(self.operator == "||"):
            return left or right

class Action:
    def __init__(self, actuator_name, value, cloud):
        self.actuator_name = actuator_name
        self.value = value
        self.cloud = cloud
    
    def execute(self):
        data = self.cloud.getDataFromCache(self.actuator_name)
        if( data is not None):
            data['data']['status'] = self.value
        self.cloud.publish(data)

class Condition:
    def __init__(self):
        self.dirty = False

    def isDirty(self):
        return self.dirty

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
        return self.left.dirty() or self.right.dirty()

    def evaluate(self):
        return self.op.process(self.left.evaluate(), self.right.evaluate())

class CloudCondition(Condition):
    def __init__(self, channel_name, cloud):
        Condition.__init__(self)
        self.cloud = cloud
        self.channel_name = channel_name
        # Get the last stored value for this channel if there is one
        data = cloud.getDataFromCache(channel_name)
        if (data is not None) and ('data' in data) and ('status' in data['data']):
            self.constant = data['data']['status']
        # Subscribe to the channel to get updates from it
        cloud.subscribe(self, channel_name)

    def evaluate(self):
        return self.constant
    
    def on_update(self, data):
        constant = self.constant
        if(data is not None) and ('data' in data) and ('status' in data['status']):
            constant = data['data']['status']
        
        if( constant != self.constant):
            self.constant = constant
            self.dirty = True
        else:
            self.dirty = False


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
            op = c['op']
            return LeftRightCondition(left, op, right)
        elif( 'channel_name' in c ):
            return CloudCondition(c['channel_name'], self.cloud)
        else:
            return None

    def parseActions(self, data):
        if(data is None):
            return None
        actions = []
        for a in data:
            if('actuator' in a) and ('value' in a):
                self.actions.append(Action(a['actuator'], a['value'], self.cloud))
        
        return actions

    def on_update(self, data):
        if VERBOSE:
            print('%s got update:' % self.name)
            print data
        
        # If the update is a rules update, parse the conditions and actions from the rules channel update
        if data['channel_name'] == self.name:
            if( 'condition' in data ):
                self.condition = self.parseCondition(data['condition'])
            if( 'actions' in data ):
                self.actions = self.parseActions(data['actions']) 
        
    


