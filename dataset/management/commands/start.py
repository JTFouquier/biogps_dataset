from django.core.management.base import BaseCommand
import urllib
import json
import os
import os.path
import zipfile
import logging
import numpy as np
from six import StringIO
from dataset import models
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from optparse import make_option
from .exp_loader import download_exp
from .exp_save import save_exp
from dataset.management.commands.exp_checker import check_exp
from dataset.management.commands.exp_loader import get_arraytype_exps
from datetime import datetime

logging.basicConfig(  
    level = logging.INFO,
    format = '[%(asctime)s, %(levelname)s, %(filename)s, L%(lineno)d] %(message)s',
    datefmt='%d-%b %H:%M',
)
ERROR_FILE = 'exp_error.txt'


class Command(BaseCommand):

    option_list = BaseCommand.option_list+(make_option("-a", "--arrays", action="store", type="string", dest="array_file", help='Specify file containing array types.',),)
    option_list = option_list+(make_option("-s", "--skip", action="store", type="string", dest="skip_file", help='Specify file containing array types to skip, only effect with -a',),)
    option_list = option_list+(make_option("-t", "--test", action="store", type="string", dest="test", help='Test the specified experiment. No database writing.',),)
    option_list = option_list+(make_option("-e", "--exp", action="store", type="string", dest="exp", help='Load the specified experiment.',),)

    def handle(self, *args, **options):
        if options['test'] is not None:
            logging.info('test experiment %s ...'%options['test'])
            if not download_exp(options['test']):
                logging.info('download experiment fail')
                return
            res = check_exp(options['test'])
            logging.info('test over, test result:')
            logging.info('%s'%res)
        elif options['array_file'] is not None:
            skip_exps = []
            if options['skip_file'] is not None:
                with open(options['skip_file'], 'r') as skipfile:
                    raw = skipfile.readlines()
                    for s in raw:
                        str = s.split('#')[0].strip()
                        if str != '':
                            skip_exps.append(str)
            with open(ERROR_FILE, 'w') as err_file:
                pass
            with open(options['array_file'], 'r') as file:
                line = file.readline().strip()
                while line != '':
                    logging.info('---process Array type: %s ---'%(line))
                    #current_platform['platform'] = line
                    exps = get_arraytype_exps(line)
                    logging.info('%d experiments in total'%(len(exps)))
                    if not len(exps)>0:
                        logging.error('no experiment for this array type')
                        return
                    #process each exps for this array type
                    for e in exps:
                        if e in skip_exps:
                            logging.info('-skip experiment %s, it\'s in skip file-'%e)
                            continue
                        logging.info('-------------------------------------------------------------------------------')
                        logging.info('-process experiment %s-'%e)
                        try:
                            models.BiogpsDatasetGeoLoaded.objects.get(geo_type=e, with_platform=line)
                            logging.info('already loaded, skip')
                            continue
                        except Exception:
                            pass
                        if not download_exp(e):
                            logging.info('download experiment fail')
                            with open(ERROR_FILE, 'a') as err_file:
                                err_file.write('%s #%s\n'%(e, 'download experiment fail'))
                                continue
                        try:
                            save_exp(e, line)
                        except Exception, excep:
                            with open(ERROR_FILE, 'a') as err_file:
                                err_file.write('%s #(%s)\n'%(e,excep))
                    line = file.readline().strip()
        elif options['exp'] is not None:
            if not download_exp(options['exp']):
                logging.info('download experiment fail')
                return
            save_exp(options['exp'])
