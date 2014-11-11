from django.core.management.base import BaseCommand
import logging
from dataset import models
from optparse import make_option
from ._exp_load import ExperimentRaw, Platform
import requests_cache
from ._exp_save import ExperimentSave
from ._exp_check import ExperimentDataParse
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s, %(levelname)s, %(filename)s, L%(lineno)d] \
      %(message)s',
    datefmt='%d-%b %H:%M',
)

if settings.CACHE_HTTP_DATA:
    requests_cache.install_cache('arrayexpress_cache')


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (make_option("-a", "--arrays", \
      action="store", type="string", dest="array_file",\
      help='Specify file containing array types.',),)
    option_list = option_list + (make_option("-s", "--skip", \
      action="store", type="string", dest="skip_file", \
      help='Specify file containing experiments to skip, only \
      works with -a',),)
    option_list = option_list + (make_option("-t", "--test", action="store",\
      type="string", dest="test", help='Test the specified experiment. \
      No database writing.',),)
    option_list = option_list + (make_option("-p", "--platform", \
      action="store", type="string", dest="platform",
      help='load experiment(s) of specified platform, can load one \
      experiment by -e, or all experiments.',),)
    option_list = option_list + (make_option("-e", "--exp", action="store", \
      type="string", dest="exp", help='Load the specified experiment.\
      must specify platform name using -p option',),)
    option_list = option_list + (make_option("-i", "--start", action="store", \
      type="string", dest="start", help='Load the first Nth experiments.\
      must specify platform name using -p option',),)



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
            for p in platforms:
                self.load_exps_of_platform(p, skips=skips)
        elif options['platform'] is not None:
            #load one experiment of this platform
            if options['exp'] is not None:
                p = Platform(options['platform'])
                p.load()
                if options['exp'] not in p.exps:
                    logging.info('experiment and platform not match')
                    return
                p.save()
                self.save_dataset(options['exp'], options['platform'], True)
                return
            #load whole experiments of this platform
            else:
                start = options['start']
                start = int(start) if start is not None else 0
                self.load_exps_of_platform(options['platform'], start)

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

    # read lines from a file, and support # comment
    def get_list_from_file(self, path):
        ret = []
        if path is None:
            return ret
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
        
    def load_exps_of_platform(self, p, start=0, skips=[]):
        po = Platform(p)
        po.load()
        po.save()
        if po.exps is None:
            logging.info('no experiments in this platform')
            return
        logging.info('%d experiments in total' % len(po.exps))
        po.exps.sort()
        for exp in po.exps[start:]:
            logging.info('No.%d experiment of total %d, %s' %\
                          (po.exps.index(exp), len(po.exps), exp))
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
                res = models.BiogpsDatasetFailed.objects.get_or_create(\
                    platform=p, dataset=exp)
                res[0].reason=e
                res[0].save()
