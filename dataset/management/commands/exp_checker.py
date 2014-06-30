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
        result['column_valid'] = len(splited)
    #E-MTAB-1169 style, skp 2 lines
    elif splited[0] == 'Hybridization REF':
        logging.info('2 lines header')
        result['row_skip'] = 2
        result['column_valid'] = len(splited)
    elif splited[0] == 'ID_REF':
        #E-GEOD-26688 style, skip columns after first 2
        if len(splited)>2 and (splited[2] in ['ABS_CALL','4w50nM-3 call']):
            logging.info('1 line header, junk from 3rd column')
            result['row_skip'] = 1
            result['column_valid'] = 2
        #most common cases E-GEOD-15568
        else:
            #logging.info('1 line header')
            result['row_skip'] = 1
            result['column_valid'] = len(splited)
    #E-MEXP-3476 style, skp 2 lines
    elif splited[0] == 'CompositeSequence Identifier':
        logging.info('1 lines header')
        result['row_skip'] = 1
        result['column_valid'] = 2
    else:
        logging.error('can NOT recognize processed data format')
        result['error'] = 'can not recognize processed data format'
    return result



def check_processed(exp, platform):
    result = {'result':True}
    exp_dir = get_exp_dir(exp)
    #header_parsed = False
    column_total = 0
    #header_line = None
    if not os.path.exists(exp_dir):
        logging.error('can NOT find %s'%(exp_dir))
        result['result'] = False
        result['error'] = 'can not locate experiment directory'
        return result
    files = os.listdir('%s%s/'%(exp_dir, platform))
    files.sort()
    for f in files:
        if f.find('processed_') == 0:
            #logging.info('check processed file %s'%f)
            with open('%s%s/%s'%(exp_dir, platform, f), 'r') as file:
                data = file.readline()
                #parse header
                res = check_processed_file_header(data)
                if 'error' in res:
                    result['result'] = False
                    result['error'] = res['error']
                    return result
                column_total = column_total + res['column_valid'] -1
    result.update(res)
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
        result['platform'] = []
        #total count of data
        if type(experiment['arraydesign']) is list:
            i = 0
            while i < len(experiment['arraydesign']):
                arraydesign = experiment['arraydesign'][i]
                result['platform'] .append(experiment['arraydesign'][i]['accession'])
                i = i+1
        else:
            result['platform'] = experiment['arraydesign']['accession']
    return result
    

def check_exp(exp, platform=None):
    logging.info('--- check experiment %s ---'%(exp))
    result = {}
    #seems useless now, check experiment
    res = check_exp_info(exp)
    if platform is None:
        if len(res['platform']) > 0:
            logging.info('multiple platforms in the experiment, please specify a platform, then run again.')
            return {'result': False}
        else:
            platform = res['platform'][0]
    result['processed'] = check_processed(exp, platform)
    #if result['exp_info']['result']==True and result['processed']['result']==True:
    if result['processed']['result']==True:
        result['result'] = True
    else:
        result['result'] = False
    logging.info('--- check experiment over ---')
    #print result
    return result
