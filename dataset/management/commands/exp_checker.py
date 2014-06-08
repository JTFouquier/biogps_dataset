import logging
import os
import json
from .exp_loader import get_exp_dir


def check_processed_file_header(header):
    splited = header.split('\t')
    result = {}
    #E-GEOD-4006 style, skp 2 lines
    if splited[0] == 'Scan REF':
        logging.info('2 lines header')
        result['row_skip'] = 2
        result['column_count'] = len(splited)
    #E-MTAB-1169 style, skp 2 lines
    elif splited[0] == 'Hybridization REF':
        logging.info('2 lines header')
        result['row_skip'] = 2
        result['column_count'] = len(splited)
    elif splited[0] == 'ID_REF':
        #E-GEOD-26688 style, skip columns after first 2
        if len(splited)>2 and (splited[2] in ['ABS_CALL','4w50nM-3 call']):
            logging.info('1 line header, junk from 3rd column')
            result['row_skip'] = 1
            result['column_count'] = 2
        #most common cases E-GEOD-15568
        else:
            logging.info('1 line header')
            result['row_skip'] = 1
            result['column_count'] = len(splited)
    #E-MEXP-3476 style, skp 2 lines
    elif splited[0] == 'CompositeSequence Identifier':
        logging.info('1 lines header')
        result['row_skip'] = 1
        result['column_count'] = 2
    else:
        logging.error('can NOT recognize processed data format')
        result['error'] = 'can not recognize processed data format'
    return result

def check_processed(exp):
    result = {'result':True}
    exp_dir = get_exp_dir(exp)
    header_parsed = False
    column_total = 0
    if not os.path.exists(exp_dir):
        logging.error('can NOT find %s'%(exp_dir))
        result['result'] = False
        result['error'] = 'can not locate experiment directory'
        return result
    for f in os.listdir(exp_dir):
        if f.find('processed_') == 0:
            #logging.info('check processed file %s'%f)
            if not header_parsed:
                with open(exp_dir+f, 'r') as file:
                    data = file.read()
                    #parse header
                    res = check_processed_file_header(data.split('\n')[0])
                    if 'error' in res:
                        result['result'] = False
                        result['error'] = res['error']
                        return result
                    result.update(res)
                    header_parsed = True
            column_total = column_total + result['column_count'] -1
    result['column_total'] = column_total
    return result


def check_exp_info(exp):
    result = {'result':True}
    exp_dir = get_exp_dir(exp)
    if not os.path.exists(exp_dir):
        logging.error('can NOT find %s'%(exp_dir))
        result['result'] = False
        result['error'] = 'can not locate experiment directory'
        return result
    with open(exp_dir+'experiment', 'r') as file:
        text = file.read()
        parsed = json.loads(text)
        if parsed['experiments']['total'] > 1:
            for e in parsed['experiments']['experiment']:
                if e['accession'] == exp:
                    experiment = e
        else:
            experiment = parsed['experiments']['experiment']
        if type(experiment['arraydesign']) is not dict:
            result['result'] = False
            result['error'] = 'experiment has more than one array type'
            return result
    return result
    

def check_exp(exp):
    logging.info('--- check experiment %s ---'%(exp))
    result = {}
    result['exp_info'] = check_exp_info(exp)
    result['processed'] = check_processed(exp)
    if result['exp_info']['result']==True and result['processed']['result']==True:
        result['result'] = True
    else:
        result['result'] = False
    logging.info('--- check experiment over ---')
    return result
