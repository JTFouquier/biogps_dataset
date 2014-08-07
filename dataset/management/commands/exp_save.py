import logging
import json
import os
import numpy as np
from dataset import models
from .exp_checker import check_exp
from django.core.exceptions import ObjectDoesNotExist


#given experiment sdrf, infomation, processed data,
#save to biogps db, note: experiment may contains
#more than one platform data, select one you want.
class ExperimentSave:

    SPECIES_MAP = {'Homo sapiens': 'human', 'Mus musculus': 'mouse',\
      'Rattus norvegicus': 'rat', 'Drosophila melanogaster': 'fruitfly', \
        'Caenorhabditis elegans': 'nematode', 'Danio rerio': 'zebrafish',\
        'Arabidopsis thaliana': 'thale-cress', 'Xenopus tropicalis': 'frog',\
         'Sus scrofa': 'pig'}

    def __init__(self, ep):
        self.data = ep.data
        #self.info = info
        self.sdrf = ep.sdrf
        self.platform = platform
        self.dataset = None

    def save_dataset(self):
        pass

    def save(self):
        self.sort_sdrf()

    #parse sample info from sdrf
    def get_sample_info(self):
        data = file.read()
        header = data.split('\n')[0]
        filter = parse_sdrf_header(header)
        data = data.split('\n')[1:]
        for d in data:
            if d == '':
                continue
            factor = {'factorvalue':{}, 'comment':{}, 'characteristics': {}}
            cel = d.split('\t')
            for k in filter['factorvalue']:
                factor['factorvalue'][k] = cel[filter['factorvalue'][k]]
            for k in filter['comment']:
                factor['comment'][k] = cel[filter['comment'][k]]
            for k in filter['characteristics']:
                factor['characteristics'][k] = cel[filter['characteristics'][k]]
            dataset['factors'].append({cel[0]:factor})

    def get_dataset(self):
        dataset = {}
        data_json = self.info
        data_json = json.loads(data)
        dataset['name'] = data_json["experiments"]["experiment"]["name"]
        dataset['summary'] = data_json["experiments"]["experiment"]["description"]["text"]
        dataset['species'] = data_json["experiments"]["experiment"]["organism"]
        dataset['arraytype'] = data_json["experiments"]["experiment"]["arraydesign"]
        try:
            dataset['secondaryaccession'] = data_json["experiments"]["experiment"]["secondaryaccession"]
        except Exception:
            dataset['secondaryaccession'] = ''
        try:
            dataset['pubmed_id'] = data_json["experiments"]["experiment"]["bibliography"]["accession"]
        except Exception:
            dataset['pubmed_id'] = ''
        dataset['factors'] = []
        with open(exp_dir+'sdrf', 'r') as file:
            data = file.read()
            header = data.split('\n')[0]
            filter = parse_sdrf_header(header)
            data = data.split('\n')[1:]
            for d in data:
                if d == '':
                    continue
                factor = {'factorvalue':{}, 'comment':{}, 'characteristics': {}}
                cel = d.split('\t')
                for k in filter['factorvalue']:
                    factor['factorvalue'][k] = cel[filter['factorvalue'][k]]
                for k in filter['comment']:
                    factor['comment'][k] = cel[filter['comment'][k]]
                for k in filter['characteristics']:
                    factor['characteristics'][k] = cel[filter['characteristics'][k]]
                dataset['factors'].append({cel[0]:factor})
        return dataset

def save_exp(exp, platform=None):
    check_res = check_exp(exp, platform)
    print check_res
    if check_res['result']==False:
        logging.error('experiment check FAIL')
        raise Exception('experiment check failed')
    logging.info('--- save experiment %s ---'%(exp))
#     logging.info('--- %d column data in total ---'%(check_res['exp_info']['column_total']))
#     if check_res['exp_info']['column_total']>MAX_SAMPLES:
#         raise Exception('more sample that we can accept')
    dataset = get_exp_info(exp)
    data_matrix = get_exp_data(exp, platform, check_res['processed'])
    #remove length incorrect lines in matrix
#     invalids = []
#     for k in data_matrix:
#         if len(data_matrix[k]) != check_res['processed']['column_total']:
#             invalids.append(k)
#     for k in invalids:
#         del data_matrix[k]
    if platform is None:
        #print dataset['arraytype']
        if dataset['arraytype'] is not dict:
            arraytype = dataset['arraytype'][0]['accession']
        else:
            arraytype = dataset['arraytype']['accession']
    else:
        arraytype = platform
    #platform
    try:
        pf = models.BiogpsDatasetPlatform.objects.get(platform=arraytype)
    except ObjectDoesNotExist:
        pf = models.BiogpsDatasetPlatform.objects.create(platform=arraytype, reporters=data_matrix.keys())
    #dataset
    meta = {'geo_gds_id':'', 'name':dataset['name'], 'factors':{}, 'default':False, 'display_params':{}, \
             'summary':dataset['summary'], 'source':BASE_URL+"experiments/" +exp, \
             'geo_gse_id':exp, 'pubmed_id':dataset['pubmed_id'], 'owner':'ArrayExpress Uploader', 'geo_gpl_id':dataset['arraytype'],\
             'secondaryaccession':dataset['secondaryaccession'], 'factors':dataset['factors']}
    try:
        ds = models.BiogpsDataset.objects.get(geo_gse_id=exp)
        ds.delete()
    except ObjectDoesNotExist:
        pass
    ds = models.BiogpsDataset.objects.create(name=dataset['name'], 
                                         summary=dataset['summary'],
                                         ownerprofile_id='arrayexpress_sid',
                                         platform=pf,
                                         geo_gds_id='',
                                         geo_gse_id=exp,
                                         geo_id_plat=exp+'_'+arraytype,
                                         metadata=meta,
                                         species=SPECIES_MAP[dataset['species']])
    #dataset data
    datasetdata = []
    for reporter in data_matrix:                        
        datasetdata.append(models.BiogpsDatasetData(dataset=ds, reporter=reporter, data=data_matrix[reporter]))
    models.BiogpsDatasetData.objects.bulk_create(datasetdata)
    ds_matrix = np.array(list(data_matrix.values()), np.float32)
    #tmp file
    s = cStringIO()
    np.save(s, ds_matrix)
    s.seek(0)
    str = s.read()
    mat = models.BiogpsDatasetMatrix(dataset=ds, reporters=list(data_matrix.keys()), matrix=str)
    mat.save()
    #finish, mark as loaded
    models.BiogpsDatasetGeoLoaded.objects.create(geo_type=exp, with_platform=arraytype, dataset=ds)
    logging.info('--- save experiment success ---')
    return

#setup data from file downloaded
def get_exp_data(exp, platform, file_format):
    data_matrix = {}
    exp_dir = get_exp_dir(exp)
    row_skip = file_format['row_skip']
    column_valid = file_format['column_valid']
    #print '%d, %d, %d, %s'%(column_skip, column_total, row_skip, column_valid)
    files = os.listdir('%s%s/'%(exp_dir, platform))
    files.sort()
    for f in files:
        if f.find('processed_') == 0:
            with open('%s%s/%s'%(exp_dir,platform,f), 'r') as file:
                rs = row_skip
                for d in file:
                    d = d.strip()
                    if rs>0 or d=='':
                        rs = rs-1
                        #print 'row skip'
                        continue
                    splited = d.split('\t')
                    if len(splited)<column_valid:
                        #print 'invalid line'
                        continue
                    reporter = splited[0]
                    if ':' in reporter:
                        reporter=reporter.split(':')[-1]
                    if reporter in data_matrix:
                        data_matrix[reporter].extend(splited[1:column_valid])
                    else:
                        data_matrix[reporter] = splited[1:column_valid]
            #print 'column total left: %d'%column_left

    invalids = []
    for a in data_matrix:
#         if len(data_matrix[a]) != column_total:
#             invalids.append(a)
#             continue
        for e in data_matrix[a]:
            #skip lines with invalid(can't convert to float)
            try:
                tmp = float(e)
            except Exception:
                invalids.append(a)
    for k in invalids:
        del data_matrix[k]
    return data_matrix

def get_exp_info(exp):
    dataset = {}
    exp_dir = get_exp_dir(exp)
    with open(exp_dir+'experiment', 'r') as file:
        data = file.read()
        data_json = json.loads(data)
        dataset['name'] = data_json["experiments"]["experiment"]["name"]
        dataset['summary'] = data_json["experiments"]["experiment"]["description"]["text"]
        dataset['species'] = data_json["experiments"]["experiment"]["organism"]
        dataset['arraytype'] = data_json["experiments"]["experiment"]["arraydesign"]
        try:
            dataset['secondaryaccession'] = data_json["experiments"]["experiment"]["secondaryaccession"]
        except Exception:
            dataset['secondaryaccession'] = ''
        try:
            dataset['pubmed_id'] = data_json["experiments"]["experiment"]["bibliography"]["accession"]
        except Exception:
            dataset['pubmed_id'] = ''
    dataset['factors'] = []
    with open(exp_dir+'sdrf', 'r') as file:
        data = file.read()
        header = data.split('\n')[0]
        filter = parse_sdrf_header(header)
        data = data.split('\n')[1:]
        for d in data:
            if d == '':
                continue
            factor = {'factorvalue':{}, 'comment':{}, 'characteristics': {}}
            cel = d.split('\t')
            for k in filter['factorvalue']:
                factor['factorvalue'][k] = cel[filter['factorvalue'][k]]
            for k in filter['comment']:
                factor['comment'][k] = cel[filter['comment'][k]]
            for k in filter['characteristics']:
                factor['characteristics'][k] = cel[filter['characteristics'][k]]
            dataset['factors'].append({cel[0]:factor})
    return dataset


def parse_sdrf_header(header):
    headers = header.split('\t')
    res = {'characteristics':{}, 'comment':{}, 'factorvalue':{}}
    i = 0
    while i<len(headers):
        h = headers[i]
        if h.find('Characteristics')==0:
            key = h.split('[')[1].split(']')[0]
            res['characteristics'][key] = i
        if h.find('Comment')==0:
            key = h.split('[')[1].split(']')[0]
            res['comment'][key] = i
        if h.find('Factor')==0:
            key = h.split('[')[1].split(']')[0]
            res['factorvalue'][key] = i
        i += 1
    return res
