'''
utils.py 

Helper functions for NetPyNE implementationf of HNN

'''

def setCfgFromFile (fn, cfg):
    d = {}
    with open(fn,'r') as fp:
        ln = fp.readlines()
        for l in ln:
            s = l.strip()
            if s.startswith('#'): continue
            sp = s.split(':')
            sp[1] = sp[1].strip()
            if len(sp[1]) > 1:
                if '.' in sp[1]:
                    try:
                        value = float(sp[1])
                    except:
                        value = str(sp[1])
                else:
                    try:
                        value = int(sp[1])
                    except:
                        value = str(sp[1])
            
            d[sp[0].strip()] = value


    for k,v in d.items():
        setattr(cfg, k, v)

    return cfg