import json 

def debugJS(thing):
    print(json.dumps(thing,indent=2,sort_keys=True))

def dumpJS(thing, fn):
    with open(fn,'w') as fh:
        fh.write(json.dumps(thing,indent=2,sort_keys=True))

def getJS(thing):
    return json.dumps(thing,indent=2,sort_keys=True)
