import logging
import os
import codecs
import requests, requests_cache
import urllib
import zipfile

WORK_DIR = {'base':'exp_loader/','downloading':'exp_loader/downloading'}

BASE_URL = "http://www.ebi.ac.uk/arrayexpress/json/v2/"

logging.basicConfig(  
    level = logging.INFO,
    format = '[%(levelname)s, L:%(lineno)d] %(message)s',
)

requests_cache.install_cache('arrayexpress_cache')

def delete_file_in_folder(src):
    for item in os.listdir(src):
        itemsrc=os.path.join(src,item)
        os.remove(itemsrc)

def unzip_file(zipfilename, unziptodir):
    if not os.path.exists(unziptodir):
        os.mkdir(unziptodir, 0777)
    zfobj = zipfile.ZipFile(zipfilename)
    i = 0
    for name in zfobj.namelist():
        name = name.replace('\\', '/')
        if name.endswith('/'):
            os.mkdir(os.path.join(unziptodir, name))
        else:
            ext_filename = os.path.join(unziptodir, 'processed_'+str(i))
            ext_dir = os.path.dirname(ext_filename)
            if not os.path.exists(ext_dir):
                os.mkdir(ext_dir, 0777)
            with open(ext_filename, 'wb') as file:
                file.write(zfobj.read(name))
            i += 1
            
def get_exp_dir(exp):
    return WORK_DIR['base']+exp+'/'

def download_exp(exp):
    logging.info('--- download experiment %s ---'%(exp))
    #create directory for download and parse usage
    if not os.path.exists(WORK_DIR['base']):
        os.makedirs(WORK_DIR['base'])
    #get experiment infomation
    url = BASE_URL+"experiments/" + exp
    logging.info('get experiment INFO from %s'%(url))
    res = requests.get(url)
    data_json = res.json()
    #experiment not exist
    if data_json['experiments']['total'] == 0:
        logging.error('can NOT find experiment: %s'%(exp))
        return False
    #initial an empty folder for this experiment
    exp_folder = WORK_DIR['base']+exp+'/'
    if os.path.exists(exp_folder):
        delete_file_in_folder(exp_folder)
    else:
        os.makedirs(exp_folder)
    with codecs.open(exp_folder+'experiment', 'w', 'utf-8') as file:
        file.write(res.text)
    #get experiment related file address
    url = BASE_URL+"files/" + exp
    logging.info('get experiment FILE ADDRESS from %s'%(url))
    res = requests.get(url)
    data_json = res.json()
    files = []
    if type(data_json["files"]["experiment"])==list:
        for e in data_json["files"]["experiment"]:
            if e["accession"] == exp:
                files = e["file"]
    else:
        files = data_json["files"]["experiment"]["file"]
    for file in files:
        #download sdrf file to db
        if file["kind"] == 'sdrf':
            logging.info('get experiment SDRF FILE from %s'%(file["url"]))
            res = requests.get(file["url"])
            with codecs.open(exp_folder+'sdrf', 'w', 'utf-8') as file:
                file.write(res.text)
        #download processed file to fs
        elif file["kind"] == 'processed':
            logging.info('get experiment PROCESSED FILE from %s'%(file["url"]))
            if os.path.exists(WORK_DIR['downloading']):
                os.remove(WORK_DIR['downloading'])
            #urllib.urlretrieve(file["url"], work_dir['downloading'])
            res = requests.get(file["url"])
            with codecs.open(exp_folder+'processed.zip', 'w') as file:
                file.write(res.content)
            #os.rename(work_dir['downloading'], exp_folder+'processed.zip')
            unzip_file(exp_folder+'processed.zip', exp_folder)
    logging.info('--- download success ---')
    return True


#from array type, get its experiment set
def get_arraytype_exps(array_type):    
    url = BASE_URL+"files?array=" + array_type
    explist = []
    logging.info('get all experiment IDs')
    logging.info('connect to %s'%(url))
#     conn = urllib2.urlopen(url)
#     data = conn.read()
#     data_json = json.loads(data)
    res = requests.get(url)
    data_json = res.json()
        
    if data_json["files"]["total-experiments"] > 0:
        experiments = data_json["files"]["experiment"]
        for experiment in experiments:
            accession = experiment["accession"]
            explist.append(accession)
    else:
        return ()
    return tuple(explist)
