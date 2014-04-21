import logging
import json
import os
import numpy as np
from dataset import models
from exp_checker import check_exp
from exp_loader import get_exp_dir, BASE_URL
from django.core.exceptions import ObjectDoesNotExist
from pkg_resources import StringIO

logging.basicConfig(  
    level = logging.INFO,
    format = '[%(levelname)s, L:%(lineno)d] %(message)s',
)

SPECIES_MAP = {'Homo sapiens':'human', 'Mus musculus':'mouse', 'Rattus norvegicus':'rat','Drosophila melanogaster':'fruitfly', \
               'Caenorhabditis elegans':'nematode', 'Danio rerio':'zebrafish', 'Arabidopsis thaliana':'thale-cress',\
               'Xenopus tropicalis':'frog', 'Sus scrofa':'pig'}

def save_exp(exp):
    check_res = check_exp(exp)
    if check_res['result']==False:
        logging.error('experiment check FAIL')
        return
    logging.info('--- save experiment %s ---'%(exp))
    dataset = get_exp_info(exp)
    data_matrix = get_exp_data(exp, check_res['processed'])
    arraytype = dataset['arraytype']['accession']
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
    with open('matrix1', 'w') as file:
        file.write(str(data_matrix))
    ds_matrix = np.array(data_matrix.values(), np.float32)
    #tmp file
    s = StringIO()
    np.save(s, ds_matrix)
    s.seek(0)
    #dataset matrix
    mat = models.BiogpsDatasetMatrix(dataset=ds, reporters=data_matrix.keys(), matrix=s.read())
    mat.save()
    #finish, mark as loaded
    models.BiogpsDatasetGeoLoaded.objects.create(geo_type=exp, with_platform=arraytype, dataset=ds)
    logging.info('--- save experiment success ---')
    return

#setup data from file downloaded
def get_exp_data(exp, precheked):
    data_matrix = {}
    exp_dir = get_exp_dir(exp)
    row_skip = precheked['row_skip']
    column_count = precheked['column_count']
    for f in os.listdir(exp_dir):
        if f.find('processed_') == 0:
            with open(exp_dir+f, 'r') as file:
                data = file.read()
                data = data.split('\n')[row_skip:]
                for d in data:
                    if d=='':
                        continue
                    splited = d.split('\t')
                    if len(splited)<column_count:
                        continue
                    reporter = splited[0]
                    if reporter in data_matrix:
                        data_matrix[reporter].extend(splited[1:column_count])
                    else:
                        data_matrix[reporter] = splited[1:column_count]
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
        except Exception,e:
            dataset['secondaryaccession'] = ''
        try:
            dataset['pubmed_id'] = data_json["experiments"]["experiment"]["bibliography"]["accession"]
        except Exception,e:
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
