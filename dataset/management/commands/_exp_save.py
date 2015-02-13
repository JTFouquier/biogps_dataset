import logging
import numpy as np
from dataset import models
from django.core.exceptions import ObjectDoesNotExist
import StringIO


class ExperimentSave:
    """
        given experiment sdrf, infomation, processed data,
        save to biogps db, note: experiment may contains
        more than one platform data, select one you want.
    """

    SPECIES_MAP = {
        'Homo sapiens': 'human', 'Mus musculus': 'mouse',
        'Rattus norvegicus': 'rat', 'Drosophila melanogaster': 'fruitfly',
        'Caenorhabditis elegans': 'nematode', 'Danio rerio': 'zebrafish',
        'Arabidopsis thaliana': 'thale-cress', 'Xenopus tropicalis': 'frog',
        'Sus scrofa': 'pig'
    }

    def __init__(self, ep):
        self.name = ep.name
        self.data = ep.data
        self.info = ep.info
        self.sdrf = ep.sdrf
        self.platform = ep.platform
        self.dataset = None

    def save(self):
        self.get_dataset_info()
        try:
            pf = models.BiogpsDatasetPlatform.objects\
                .get(platform=self.platform)
        except ObjectDoesNotExist:
            raise Exception('platform does not exist.')
        # dataset
        dataset = self.dataset
        if type(dataset['arraytype']) is list:
            for e in dataset['arraytype']:
                if e['accession'] == self.platform:
                    dataset['arraytype'] = e
        # get sample count and factor count and factor contents
        factors = dataset['factors']
        sample_count = len(factors)
        factor_count = 0
        fvs = []
        for e in factors:
            e = e[e.keys()[0]]
            if 'factorvalue' not in e:
                break
            fvs.append(e['factorvalue'])
        if len(fvs) > 0:
            factor_count = len(fvs[0].keys())

        meta = {
            'geo_gds_id': '', 'name': dataset['name'],
            'default': False, 'display_params': {},
            'summary': dataset['summary'], 'source':
            "http://www.ebi.ac.uk/arrayexpress/json/v2/experiments/"
            + self.name, 'geo_gse_id': self.name, 'pubmed_id':
            dataset['pubmed_id'], 'owner': 'ArrayExpress Uploader',
            'geo_gpl_id': dataset['arraytype'], 'secondaryaccession':
            dataset['secondaryaccession'], 'factors': dataset['factors']}
        ds = models.BiogpsDataset.objects.create(
            name=dataset['name'],
            summary=dataset['summary'],
            ownerprofile_id='arrayexpress_sid',
            platform=pf,
            geo_gds_id='',
            geo_gse_id=self.name,
            geo_id_plat=self.name + '_' + self.platform,
            metadata=meta,
            species=self.SPECIES_MAP[dataset['species']],
            sample_count=sample_count,
            factor_count=factor_count,
            factors=fvs)
        # dataset data
        datasetdata = []
        for idx in self.data.index:
            datasetdata.append(models.BiogpsDatasetData(
                dataset=ds, reporter=idx,
                data=list(self.data.loc[idx, :].values)))
        models.BiogpsDatasetData.objects.bulk_create(datasetdata)
        # tmp file
        s = StringIO.StringIO()
        np.save(s, self.data.values)
        s.seek(0)
        mat = models.BiogpsDatasetMatrix(
            dataset=ds,
            reporters=list(self.data.index), matrix=s.read())
        mat.save()
        # finish, mark as loaded
        models.BiogpsDatasetGeoLoaded.objects.create(
            geo_type=self.name,
            with_platform=self.platform, dataset=ds)
        logging.info('--- save experiment success ---')
        return

    # get experiment infomation from info and sdrf
    def get_dataset_info(self):
        dataset = {}
        data_json = self.info
        dataset['name'] = data_json["experiments"]["experiment"]["name"]
        dataset['summary'] =\
            data_json["experiments"]["experiment"]["description"]["text"]
        dataset['species'] = data_json["experiments"]["experiment"]["organism"]
        dataset['arraytype'] =\
            data_json["experiments"]["experiment"]["arraydesign"]
        try:
            dataset['secondaryaccession'] =\
                data_json["experiments"]["experiment"]["secondaryaccession"]
        except Exception:
            dataset['secondaryaccession'] = ''
        try:
            dataset['pubmed_id'] =\
                data_json["experiments"]["experiment"]\
                ["bibliography"]["accession"]
        except Exception:
            dataset['pubmed_id'] = ''
        dataset['factors'] = []

        ks = self.parse_sdrf_header(list(self.sdrf.columns))
        for d in self.sdrf.index:
            factor = {'factorvalue': {}, 'comment': {}, 'characteristics': {}}
            cel = self.sdrf.loc[d]
            for k in ks['factorvalue']:
                factor['factorvalue'][k] = cel[ks['factorvalue'][k]]
            for k in ks['comment']:
                factor['comment'][k] = cel[ks['comment'][k]]
            for k in ks['characteristics']:
                factor['characteristics'][k] = cel[ks['characteristics'][k]]
            dataset['factors'].append({cel[0]: factor})
        self.dataset = dataset

    def parse_sdrf_header(self, headers):
        res = {'characteristics': {}, 'comment': {}, 'factorvalue': {}}
        i = 0
        while i < len(headers):
            h = headers[i]
            if h.find('Characteristics') == 0:
                key = h.split('[')[1].split(']')[0]
                res['characteristics'][key] = i
            if h.find('Comment') == 0:
                key = h.split('[')[1].split(']')[0]
                res['comment'][key] = i
            if h.find('Factor') == 0:
                key = h.split('[')[1].split(']')[0]
                res['factorvalue'][key] = i
            i += 1
        return res
