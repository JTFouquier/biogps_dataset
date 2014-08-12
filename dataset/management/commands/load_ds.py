from django.core.management.base import BaseCommand
import logging
from dataset import models
from optparse import make_option
from ._exp_load import ExperimentRaw, Platform
import requests_cache
from ._exp_save import ExperimentSave
from ._exp_check import ExperimentDataParse
from django.core.exceptions import ObjectDoesNotExist

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s, %(levelname)s, %(filename)s, L%(lineno)d] \
      %(message)s',
    datefmt='%d-%b %H:%M',
)

CACHE = True

if CACHE:
    requests_cache.install_cache('arrayexpress_cache')


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

    ERROR_FILE = 'exp_error.txt'

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
            platforms = self.get_list_from_file(options['array_file'])
            skips = self.get_list_from_file(options['skip_file'])
            if platforms is None:
                return
            for p in platforms:
                po = Platform(p)
                po.load()
                po.save()
                if po.exps is None:
                    continue
                for exp in po.exps:
                    if exp in skips:
                        logging.info('skip %s' % exp)
                        continue
                    if self.is_already_loaded(exp):
                        logging.info('existed %s' % exp)
                        continue
                    try:
                        self.save_dataset(exp, p)
                    except Exception, e:
                        logging.error('Exception: %s' % e)
                        with open(self.ERROR_FILE, 'a') as f:
                            f.write('%s #%s\n' % (exp, e))
                        continue
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
            self.save_dataset(options['exp'], options['platform'], True)
            return

    def save_dataset(self, name, platform, dump=False):
        logging.info('--- start %s ---' % name)
        #clear dataset if already exists
        ds = models.BiogpsDataset.objects.filter(geo_gse_id=name)
        ds.delete()
        er = ExperimentRaw(name)
        er.load()
        logging.info('parse data')
        if dump:
            er.dump()
        ep = ExperimentDataParse(er, platform)
        ep.parse()
        logging.info('save data')
        es = ExperimentSave(ep)
        es.save()
        logging.info('--- done ---')
        return

    #read lines from a file, and support # comment
    def get_list_from_file(self, path):
        ret = None
        with open(path, 'r') as f:
            raw = f.readlines()
            if len(raw) > 0:
                ret = []
                for s in raw:
                    s = s.strip()
                    if len(s) <= 0:
                        continue
                    ret.append(s.split('#')[0].strip())
        return ret

    def is_already_loaded(self, exp):
        try:
            models.BiogpsDatasetGeoLoaded.objects.get(geo_type=exp)
            return True
        except ObjectDoesNotExist:
            return False
