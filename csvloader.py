import csv
import json
import re

def arrayToHashByIndex(ary):
    h = {}
    idx = 0
    for aval in ary:
        h[aval] = idx
        idx += 1
    return h

def namesAndValsToHash(names, vals):
    idx = 0;
    h = {}
    for name in names:
        if idx < len(vals):
            h[name] = vals[idx]
        else:
            h[name] = ''
        idx += 1
    return h

def load(fn, dialect = None):
    result = []
    try:
        with open(fn,'r',encoding='utf-8-sig') as fh:
            if dialect == 'tsv':
                reader = csv.reader(fh,dialect=csv.excel_tab)
            else:
                reader = csv.reader(fh)

            rownum = 0
            colnames = []
            for row in reader:
                if rownum == 0:
                    colnames = row
                else:
                    if len(row):
                        comment = re.match(r'#', row[0])
                        if not comment:
                            result.append(namesAndValsToHash(colnames,row))
                rownum += 1
    except Exception as e:
        print('Could not open file: ' + fn)
        print(e)

    return result


# turn something into a string one way or another. Dicts get json'd
# arrays that contains only strings get joined with commas, otherwise
# they get json'd, too, and everything else gets to just be a str
def my_stringify(thing):
    ostr = ''
    if isinstance(thing,list) or isinstance(thing,tuple):
        nonstrings = False
        for elem in thing:
            if not isinstance(elem,str):
                nonstrings = True
                break;
        if nonstrings:
            ostr = json.dumps(thing)
        else:
            ostr = ', '.join(thing)

    elif isinstance(thing,dict):
        ostr = json.dumps(thing)
    else:
        ostr = str(thing)

    return ostr


def dump(data,fn,colnames = None, dialectname = None):
    if colnames is None:
        ch = {}
        for datum in data:
            dkeys = datum.keys()
            for dkey in dkeys:
                ch[dkey] = True
        colnames = list(ch.keys())

    try:
        with open(fn,'w') as fh:
            if dialectname == 'tsv':
                writer = csv.writer(fh, dialect=csv.excel_tab)
            else:
                writer = csv.writer(fh)

            writer.writerow(colnames)
            for datum in data:
                row = [ my_stringify(datum.get(x,'')) for x in colnames ]
                writer.writerow(row)
    except Exception as e:
        print('-err- Exception writing csv')
        print(e)



