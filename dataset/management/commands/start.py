from django.core.management.base import BaseCommand
import urllib
import urllib2
import json
import os
import os.path
import zipfile
import logging
import numpy as np
from StringIO import StringIO
from dataset import models
from django.core.exceptions import ObjectDoesNotExist


logging.basicConfig(  
    level = logging.INFO,
    format = '[%(levelname)s, L:%(lineno)d] %(message)s',
)  

species_map = {'Homo sapiens':'human', 'Mus musculus':'mouse', 'Rattus norvegicus':'rat','Drosophila melanogaster':'fruitfly', \
               'Caenorhabditis elegans':'nematode', 'Danio rerio':'zebrafish', 'Arabidopsis thaliana':'thale-cress',\
               'Xenopus tropicalis':'frog', 'Sus scrofa':'pig'}

def help_message():
    return 'Usage: python manage.py start file <path-to-array-type-file> [skip <path-to-experiments-file>]\
 or python manage.py start exp <experiment-id>'

class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            type = args[0]
            name = args[1]
        except Exception:
            print help_message()
            return
        try:
            skipcmd = args[2]
            skipname = args[3]
            skip = True
        except Exception:
            skip = False

        if type == 'exp':
            logging.info('dry run on experiment %s, no database savings'%name)
            dataset = get_exp_info(name)
            get_exp_sample_file(name)
            data_matrix = setup_dataset(name)
            print data_matrix
            logging.info('dry run over')
        elif type == 'file':
            if skip:
                skip_exps = []
                with open(skipname, 'r') as skipfile:
                    skip_exps = skipfile.readlines()
            with open(name, 'r') as file:
                line = file.readline().strip()
                while line != '':
                    logging.info('---process Array type: %s ---'%(line))
                    #current_platform['platform'] = line
                    exps = get_arraytype_exps(line)
                    logging.info('%d experiments in total'%(len(exps)))
                    if not len(exps)>0:
                        raise Exception, 'no experiment for this array type'
                    #create directory for download and parse usage
                    if not os.path.exists('tmp/'):
                        os.makedirs('tmp/')
                        os.makedirs('tmp/sample/')
                        os.makedirs('tmp/unzip_sample/')
                    #process each exps for this array type
                    for e in exps:
                        if skip and e+'\n' in skip_exps:
                            logging.info('-skip experiment %s, it\'s in skip file-'%e)
                            continue
                        logging.info('-process experiment %s-'%e)
                        try:
                            models.BiogpsDatasetGeoLoaded.objects.get(geo_type=e, with_platform=line)
                            logging.info('already loaded, skip')
                            continue
                        except Exception:
                            pass
                        dataset = get_exp_info(e)
                        get_exp_sample_file(e)
                        logging.debug('setup_dataset')
                        data_matrix = setup_dataset(e)
                        #print data_matrix
                        logging.info('write database')
                        #platform
                        try:
                            pf = models.BiogpsDatasetPlatform.objects.get(platform=line)
                        except ObjectDoesNotExist:
                            pf = models.BiogpsDatasetPlatform.objects.create(platform=line, reporters=data_matrix.keys())
                        #dataset
                        meta = {'geo_gds_id':'', 'name':dataset['name'], 'factors':{}, 'default':False, 'display_params':{}, \
                                 'summary':dataset['summary'], 'source':"http://www.ebi.ac.uk/arrayexpress/json/v2/experiments/" + e, \
                                 'geo_gse_id':e, 'pubmed_id':dataset['pubmed_id'], 'owner':'ArrayExpress Uploader', 'geo_gpl_id':line,\
                                 'secondaryaccession':dataset['secondaryaccession'], 'factors':dataset['factors']}
                        try:
                            ds = models.BiogpsDataset.objects.get(geo_gse_id=e)
                            ds.delete()
                        except ObjectDoesNotExist:
                            pass                 
                        ds = models.BiogpsDataset.objects.create(name=dataset['name'], 
                                                             summary=dataset['summary'],
                                                             ownerprofile_id='arrayexpress_sid',
                                                             platform=pf,
                                                             geo_gds_id='',
                                                             geo_gse_id=e,
                                                             geo_id_plat=e+'_'+line,
                                                             metadata=meta,
                                                             species=species_map[dataset['species']])
                        #dataset data
                        datasetdata = []
                        for reporter in data_matrix:                        
                            datasetdata.append(models.BiogpsDatasetData(dataset=ds, reporter=reporter, data=data_matrix[reporter]))
                        models.BiogpsDatasetData.objects.bulk_create(datasetdata)
                        ds_matrix = np.array(data_matrix.values(), np.float32)
                        #tmp file
                        s = StringIO()
                        np.save(s, ds_matrix)
                        s.seek(0)
                        #dataset matrix
                        mat = models.BiogpsDatasetMatrix(dataset=ds, reporters=data_matrix.keys(), matrix=s.read())
                        mat.save()
                        #finish, mark as loaded
                        models.BiogpsDatasetGeoLoaded.objects.create(geo_type=e, with_platform=line, dataset=ds)
                    line = file.readline().strip()
        else:
            print help_message()
#from array type, get its experiment set
def get_arraytype_exps(array_type):    
    url = "http://www.ebi.ac.uk/arrayexpress/json/v2/files?array=" + array_type
    explist = []
    logging.info('get all experiment IDs')
    logging.info('connect to %s'%(url))
    conn = urllib2.urlopen(url)
    data = conn.read()
    data_json = json.loads(data)
        
    if data_json["files"]["total-experiments"] > 0:
        experiments = data_json["files"]["experiment"]
        for experiment in experiments:
            accession = experiment["accession"]
            explist.append(accession)
    else:
        return ()
    return tuple(explist)

def get_exp_info(exp):
    url = "http://www.ebi.ac.uk/arrayexpress/json/v2/experiments/" + exp
    dataset = {}
    logging.info('get experiment info from %s'%(url))
    conn = urllib2.urlopen(url)
    data = conn.read()
    data_json = json.loads(data)
    dataset['name'] = data_json["experiments"]["experiment"]["name"]
    dataset['summary'] = data_json["experiments"]["experiment"]["description"]["text"]
    dataset['species'] = data_json["experiments"]["experiment"]["organism"]
    dataset['secondaryaccession'] = data_json["experiments"]["experiment"]["secondaryaccession"]
    try:
        dataset['pubmed_id'] = data_json["experiments"]["experiment"]["bibliography"]["accession"]
    except Exception,e:
        dataset['pubmed_id'] = ''
    #get experiment factorsd
    url = "http://www.ebi.ac.uk/arrayexpress/json/v2/files/" + exp
    logging.info('get experiment file info from %s'%(url))
    conn = urllib2.urlopen(url)
    data = conn.read()
    data_json = json.loads(data)
    files = data_json["files"]["experiment"]["file"]
    dataset['factors'] = []
    for file in files:
        if file["kind"] == u'sdrf':
            logging.info('get experiment sdrf file from %s'%(file["url"]))
            conn = urllib2.urlopen(file["url"])
            data = conn.read()            
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

#get all data for the experiment and set up data in database
def get_exp_sample_file(exp):

    url = "http://www.ebi.ac.uk/arrayexpress/json/v2/files/" + exp
    logging.info('get experiment file info from %s'%(url))
    conn = urllib2.urlopen(url)
    data = conn.read()
    data_json = json.loads(data)
    experiment = data_json["files"]["experiment"]
    if isinstance(experiment, list):
        files = experiment[0]["file"]
    else:
        files = experiment["file"]
    for file in files:
        if file["kind"] == u'processed':
            dest = "tmp/sample/" + file["name"]
            if not os.path.exists(dest):
                logging.info('get sample file: %s'%(file["url"]))
                urllib.urlretrieve(file["url"], dest)
                unzip_file("tmp/sample/" + file["name"], "tmp/unzip_sample/" + exp)
            else:                
                logging.info('sample file exists')
            #setup_dataset(exp) 
    logging.debug('leave get_exp_sample_file')

#setup data from file downloaded
def setup_dataset(exp):  
    path = 'tmp/unzip_sample/' + exp
    dir = os.listdir(path)
    dir.sort()
    data_matrix = {}
    for f in dir:
        with open(path+'/'+f, 'r') as file:
            line = file.readline().strip()
            first_line = True
            ending = len(line.split('\t'))
            while line != '':
                splited = line.split('\t')
                #check format, and skip first line
                if first_line:                    
                    first_line = False
                    line = file.readline().strip()
                    #E-GEOD-4006 style, skp 2 lines
                    if splited[0] == 'Scan REF':
                        line = file.readline().strip()
                    #E-GEOD-26688 style, skip last 2 columns
                    elif len(splited)>2 and splited[2] == 'ABS_CALL':
                        ending = 2
                    continue
                #make sure data is digital
                i = 1
                while i<ending:
                    try:
                        splited[i] = float(splited[i])
                        i += 1
                    except ValueError, e:
                        print splited
                        raise Exception, 'file format wrong, check columns of file:%s'%(path+'/'+f)
                reporter = splited[0]
                if reporter in data_matrix:
                    data_matrix[reporter].extend(splited[1:ending])
                else:
                    data_matrix[reporter] = splited[1:ending]
                line = file.readline().strip()
            return data_matrix
    return data_matrix


def unzip_file(zipfilename, unziptodir):
    if not os.path.exists(unziptodir):
        os.mkdir(unziptodir, 0777)
    zfobj = zipfile.ZipFile(zipfilename)
    for name in zfobj.namelist():
        name = name.replace('\\', '/')
        if name.endswith('/'):
            os.mkdir(os.path.join(unziptodir, name))
        else:
            ext_filename = os.path.join(unziptodir, name)
            ext_dir = os.path.dirname(ext_filename)
            if not os.path.exists(ext_dir):
                os.mkdir(ext_dir, 0777)
            outfile = open(ext_filename, 'wb')
            outfile.write(zfobj.read(name))
            outfile.close()
