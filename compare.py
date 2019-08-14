def compare(source_file, target_file, source_key=None, target_key=None):
    from deepdiff import DeepDiff
    from pprint import pprint
    import json
    import pickle

    with open(source_file, 'r') as fileObj:
        if source_file.endswith('.json'):
            source = json.load(fileObj)
        elif source_file.endswith('.pkl'):
            source = pickle.load(fileObj)
    if source_key: source = source[source_key]

    with open(target_file, 'r') as fileObj:
        if target_file.endswith('.json'):
            target = json.load(fileObj)
        elif source_file.endswith('.pkl'):
            target = pickle.load(fileObj)
    if target_key: target = target[target_key]
    
    ddiff = DeepDiff(source, target)#, significant_digits=1)#, ignore_order=1)#, report_repetition=True)  # verbose_level=1, view='tree'
    pprint(ddiff)
    return ddiff

compareSecs = 1
compareConns = 0
compareL5Pyr = 0

if compareSecs:
    source = 'hnn_secs_orig.json'  
    target = 'netpyne/hnn_secs_netpyne.json'  
    compare(source, target)

if compareConns:
    source = 'hnn_conns_orig.json' # conns
    target = 'netpyne/hnn_conns_netpyne.json' #conns
    compare(source, target)

if compareL5Pyr:
    source = 'netpyne/L5Pyr_rule_hnn.json'  
    target = 'netpyne/L5Pyr_rule_netpyne.json'  
    compare(source, target)
