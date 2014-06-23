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
            logging.info('1 line header')
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

def check_processed(exp, c_s, c_t):
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
    files = os.listdir(exp_dir)
    files.sort()
    for f in files:
        if f.find('processed_') == 0:
            #logging.info('check processed file %s'%f)
            with open(exp_dir+f, 'r') as file:
                data = file.readline()
#                 if header_line is None:
#                     header_line = data
#                 else:
#                     if header_line != data:
#                         result['result'] = False
#                         result['error'] = 'processed file format inconsistent'
#                         return result
                #if not header_parsed:
                #parse header
                res = check_processed_file_header(data)
                if 'error' in res:
                    result['result'] = False
                    result['error'] = res['error']
                    return result
                if c_s > 0:
                    c_s = c_s - res['column_valid']
                column_total = column_total + res['column_valid'] -1
                if column_total == c_t:
                    break
                #result.update(res)
                #header_parsed = True
            #column_total = column_total + result['column_count'] -1
    if column_total != c_t:
        result['result'] = False
        result['error'] = 'column in processed data not correct'
    else:
        result.update(res)
    return result


def check_exp_info(exp, platform):
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
        colum_skip = 0
        #total count of data
        if platform is not None:
            if type(experiment['arraydesign']) is list:
                i = 0
                while i < len(experiment['arraydesign']):
                    arraydesign = experiment['arraydesign'][i]
                    if arraydesign['accession'] == platform:
                        result['column_total'] = arraydesign['count']
                        result['column_skip'] = colum_skip
                        break
                    else:
                        colum_skip = colum_skip + arraydesign['count']
                    i = i+1
            else:
                result['column_total'] = arraydesign['count']
                result['column_skip'] = 0
        #plat form is None, take 1st platform
        else:
            if type(experiment['arraydesign']) is not dict:
                arraydesign = experiment['arraydesign'][0]
            else:
                arraydesign = experiment['arraydesign']
            result['column_total'] = arraydesign['count']
            result['column_skip'] = 0
    return result
    

def check_exp(exp, platform=None):
    logging.info('--- check experiment %s ---'%(exp))
    result = {}
    result['exp_info'] = check_exp_info(exp, platform)
    result['processed'] = check_processed(exp, result['exp_info']['column_skip'], result['exp_info']['column_total'])
    if result['exp_info']['result']==True and result['processed']['result']==True:
        result['result'] = True
    else:
        result['result'] = False
    logging.info('--- check experiment over ---')
    print result
    return result
