# -*- coding: utf-8 -*-

from django.core.management.base import NoArgsCommand
from django.conf import settings
from dataset.models import BiogpsDataset
import urllib
import urllib2
from tagging.models import Tag


class Command(NoArgsCommand):
    help = 'A utility that tags datasets based on NCBO annotations.'
    # Turn off Django's DEBUG mode to limit memory usage
    settings.DEBUG = False

    def handle_noargs(self, **options):
        def get_param_vals(params, res_str):
            """Return value for param, parsed from NCBO res_str"""
            _annos = {}
            for p in params:
                try:
                    p_pos = res_str.index(p)
                    p_val = res_str[p_pos:].split(': ', 1)[1].split(',', 1)[0]
                    if p == 'localConceptId':
                        p_val = p_val.split(':')[0]
                    if p == 'preferredName':
                        p_val = p_val.lower()
                    _annos[p] = p_val
                except ValueError:
                    # Param not found in string
                    continue
            return _annos

        def read_fma_file():
            """Load fma subset from file"""
            _fma_annos = {}
            with open('fma_anatomy.txt') as f:
                for line in f:
                    try:
                        int(line[0])
                        s_line = line.strip('\n').split('\t')
                        _fma_annos[s_line[2]] = s_line[1]
                    except ValueError:
                        # Metadata or blank line
                        continue
            return _fma_annos

        def update_ds_annos(annos):
            """Compare annotations to previously parsed annotations,
               update if necessary"""
            if annos['preferredName'] not in prev_annos['preferredName']:
                ds_annos.append(annos)

        # NCBO annotator web service
        API_KEY = settings.NCBO_ANNO_KEY
        annotator_url = 'http://data.bioontology.org/annotator'
        all_ds_annos = {}
        # all_ds_freqs = {}
        # doid_freqs = {}
        # fma_freqs = {}
        self.stdout.write('\nLoading datasets...\n')

        # Read in fma susbset from file: {"full_id": "preferred_name"}
        fma_annos = read_fma_file()
        if not fma_annos:
            print('No fma annotations found, quitting.')
            return
        fma_full_ids = fma_annos.keys()

        # Terms to skip in DOID and fma ontologies
        skip_terms = ['body', 'cell', 'chronic rejection of renal transplant',
                      'cytoplasm', 'disease', 'genome', 'organ', 'syndrome']

        # Annotate datasets
        ds = BiogpsDataset.objects.all().order_by('-created')
        watch = ['immune system', 'nervous system']
        i = 0
        for d in ds:
            print 'No.%d' % i
            print 'id:%s, geo_gse_id:%s' % (d.id, d.geo_gse_id)
            # skip already tagged ones
            ts = Tag.objects.get_for_object(ds)
            if ts.count() > 0:
                print 'already tagged'
                continue
            summary = d.summary.encode('utf-8')
            if summary:
                # Get annotation(s) for current summary
                all_ds_annos[d.id] = []
                params = {
                      # 'longestOnly': 'false',
                      # 'wholeWordOnly': 'true',
                      # 'withContext': 'true',
                      # 'filterNumber': 'true',
                      # 'stopWords': '',
                      # 'withDefaultStopWords': 'false',
                      # 'isStopWordsCaseSenstive': 'false',
                      # 'minTermSize': '3',
                      # 'scored': 'true',
                      # 'withSynonyms': 'true',
                      # 'ontologiesToExpand': '1053,1009',
                      # 'ontologiesToKeepInResult': '1053,1009',
                      # 'isVirtualOntologyId': 'true',
                      # 'semanticTypes': '',
                      # 'levelMax': '0',
                      # 'mappingTypes': 'null',
                      # 'textToAnnotate': summary,
                      # 'format': 'tabDelimited',
                      'text': summary,
                      'apikey': API_KEY,
                      'ontologies': 'FMA,DOID',
                }
                data = urllib.urlencode(params)
                conn = urllib2.urlopen(annotator_url, data)
                anno_results = conn.read()
                conn.close()

                # Previous annotations for quick reference
                prev_annos = {}

                # Dataset unique annotations
                ds_annos = []

                # Dataset tags
                ds_tags = set()

                params = ['conceptId', 'fullId', 'localConceptId',
                          'localOntologyId', 'preferredName']
                import json
                jsn = json.loads(anno_results)
                for j in jsn:
                    ds_tags.add(j['annotations'][0]['text'])
                # tagging using django-tagging
                for e in ds_tags:
                    # print '"%s"' % e.lower()
                    if e in watch:
                        print e
                    Tag.objects.add_tag(d, '"%s"' % e.lower())
            else:
                print 'summary wrong'
