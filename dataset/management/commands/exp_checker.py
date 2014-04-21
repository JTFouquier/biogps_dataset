import logging
import os
import json
from exp_loader import get_exp_dir

logging.basicConfig(  
    level = logging.INFO,
    format = '[%(levelname)s, %(filename), L:%(lineno)d] %(message)s',
)




def check_processed(exp):
    result = {'result':True}
    exp_dir = get_exp_dir(exp)
    if not os.path.exists(exp_dir):
        logging.error('can NOT find %s'%(exp_dir))
        result['result'] = False
        result['error'] = 'can not locate experiment directory'
        return result
    for f in os.listdir(exp_dir):
        if f.find('processed_') == 0:
            with open(exp_dir+f, 'r') as file:
                line = file.readline().strip()
                splited = line.split('\t')
                #E-GEOD-4006 style, skp 2 lines
                if splited[0] == 'Scan REF':
                    logging.info('2 lines header')
                    result['row_skip'] = 2
                    result['column_count'] = len(splited)
                    return result
                #E-MTAB-1169 style, skp 2 lines
                elif splited[0] == 'Hybridization REF':
                    logging.info('2 lines header')
                    result['row_skip'] = 2
                    result['column_count'] = len(splited)
                    return result
                elif splited[0] == 'ID_REF':
                    #E-GEOD-26688 style, skip columns after first 2
                    if len(splited)>2 and splited[2] == 'ABS_CALL':
                        logging.info('1 line header, junk from 3rd column')
                        result['row_skip'] = 1
                        result['column_count'] = 2
                        return result
                    #most common cases E-GEOD-15568
                    else:
                        logging.info('1 line header')
                        result['row_skip'] = 1
                        result['column_count'] = len(splited)
                        return result
                else:
                    logging.error('can NOT recognize processed data format')
                    logging.error('%s',line)
                    result['result'] = False
                    result['error'] = 'can not recognize processed data format'
                    return result
    result['result'] = False
    result['error'] = 'can not find processed files'
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
        if type(parsed['experiments']['experiment']['arraydesign']) is not dict:
            result['result'] = False
            result['error'] = 'experiment has more than one array type'
            return 
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
