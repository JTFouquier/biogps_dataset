from django.core.management.base import BaseCommand
import logging
import numpy as np
from six import StringIO
from dataset import models
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from optparse import make_option
#from .exp_save import save_exp
#from dataset.management.commands.exp_checker import check_exp
from dataset.management.commands.exp_loader import ExperimentRaw, Platform
from datetime import datetime
import requests
import string
import requests_cache
from dataset.management.commands.exp_save import ExperimentSave
from dataset.management.commands.exp_checker import ExperimentDataParse

logging.basicConfig(
    level = logging.INFO,
    format = '[%(asctime)s, %(levelname)s, %(filename)s, L%(lineno)d] \
      %(message)s',
    datefmt='%d-%b %H:%M',
)
ERROR_FILE = 'exp_error.txt'
requests_cache.install_cache('arrayexpress_cache')




#read lines from a file, and support # comment
def get_list_from_file(path):
    ret = None
    with open(path, 'r') as f:
        raw = f.readlines()
        if len(raw) > 0:
            ret = []
            for s in raw:
                ret.append(s.split('#')[0].strip())
    return ret


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (make_option("-a", "--arrays", \
      action="store", type="string", dest="array_file",\
      help='Specify file containing array types.',),)
    option_list = option_list + (make_option("-s", "--skip", \
      action="store", type="string", dest="skip_file", \
      help='Specify file containing array types to skip, only \
      effect with -a',),)
    option_list = option_list + (make_option("-t", "--test", action="store",\
      type="string", dest="test", help='Test the specified experiment. \
      No database writing.',),)
    option_list = option_list + (make_option("-e", "--exp", action="store", \
      type="string", dest="exp", help='Load the specified experiment.\
      must specify platform name using -p option',),)
    option_list = option_list + (make_option("-p", "--platform", \
      action="store", type="string", dest="platform",
      help='use data from specified platform, go with -e, -t',),)

    def handle(self, *args, **options):
        if options['test'] is not None:
            er = ExperimentRaw(options['test'])
            er.load()
            if er.data is not None:
                logging.info('experiment load and check success')
            else:
                logging.info('test over, fail')
        elif options['array_file'] is not None:
            #skips = get_list_from_file(options['skip_file'])
            platforms = get_list_from_file(options['array_file'])
            if platforms is None:
                return
            for e in platforms:
                p = Platform(e)
                p.load()
                if p.exps is None:
                    continue
                for exp in p.exps:
                    er = ExperimentRaw(exp)
                    er.load()
                    print er.data
            return
        elif options['exp'] is not None:
            if options['platform'] is None:
                logging.error('specify a plotform name by -p')
                return
            p = Platform(options['platform'])
            p.load()
            if options['exp'] not in p.exps:
                logging.info('experiment and platform not match')
                return
            p.save()
            er = ExperimentRaw(options['exp'])
            er.load()
            #er.dump()
            ep = ExperimentDataParse(er, options['platform'])
            ep.parse()
            es = ExperimentSave(ep)
            es.save()
            return
