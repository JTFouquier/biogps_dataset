from django.core.management.base import BaseCommand
import urllib
import urllib2
import json
import os
import os.path
import zipfile
from dataset import models

#current_platform = {}
dataset = {}
data_matrix = {}

#E-GEOD-4006 
class Command(BaseCommand):
    def handle(self, *args, **options):
        if len(args) == 0:
            print 'Usage: python manage.py start <path-to-array-type-file>'
            return
        try:
            file = open(args[0], 'r')
        except IOError, e:
            print e
            return
        print 'Array type file open'
        line = file.readline().strip()
        while line != '':
            print '---process Array type: '+line+' ---'
            #current_platform['platform'] = line
            exps = get_arraytype_exps(line)
            print '%d experiments in total'%(len(exps))
            if not len(exps)>0:
                print 'WARNING: array type %s has not experiments!'%(line)
                file.close()
                return
            #create directory for download and parse usage
            if not os.path.exists('tmp/'):
                os.makedirs('tmp/')
                os.makedirs('tmp/sample/')
                os.makedirs('tmp/unzip_sample/')
            #process each exps for this array type
            for e in exps:
                print '-process experiment %s-'%e
                ret = get_exp_sample_file(e)
                if not ret:
                    file.close()
                    print 'cannot get sample file for experiment: %s'%(e)
                    return
                ret = setup_dataset(e)
                if not ret:
                    file.close()
                    print 'set up data fail for experiment: %s'%(e)
                    return
                #print data_matrix
                ds = models.BiogpsDataset.objects.create(name=dataset['name'], summary=dataset['summary'])
                for reporter in data_matrix:
                    models.BiogpsDatasetData.objects.create(dataset=ds, reporter=reporter, data=data_matrix[reporter])                    
            line = file.readline().strip()

#from array type, get its experiment set
def get_arraytype_exps(array_type):    
    url = "http://www.ebi.ac.uk/arrayexpress/json/v2/files?array=" + array_type
    explist = []
    print 'get all experiment IDs'
    try:
        print 'connect to %s'%(url)
        conn = urllib2.urlopen(url)
        data = conn.read()
        data_json = json.loads(data)
    except Exception, e:
        return None
    if data_json["files"]["total-experiments"] > 0:
        experiments = data_json["files"]["experiment"]
        for experiment in experiments:
            accession = experiment["accession"]
            explist.append(accession)
    else:
        return ()
    return tuple(explist)

#get all data for the experiment and set up data in database
def get_exp_sample_file(exp):
    try:
        url = "http://www.ebi.ac.uk/arrayexpress/json/v2/experiments/" + exp
        print 'get experiment info from %s'%(url)
        conn = urllib2.urlopen(url)
        data = conn.read()
        data_json = json.loads(data)
    except Exception, e:
        print e
        return False    
    dataset['name'] = data_json["experiments"]["experiment"]["name"]
    dataset['summary'] = data_json["experiments"]["experiment"]["description"]["text"]  

    try:
        url = "http://www.ebi.ac.uk/arrayexpress/json/v2/files/" + exp
        print 'get experiment file info from %s'%(url)
        conn = urllib2.urlopen(url)
        data = conn.read()
        data_json = json.loads(data)
    except Exception, e:
        print e
        return False
    experiment = data_json["files"]["experiment"]
    if isinstance(experiment, list):
        samplefiles = experiment[0]["file"]
    else:
        samplefiles = experiment["file"]
    for samplefile in samplefiles:
        if samplefile["kind"] == u'processed':
            dest = "tmp/sample/" + samplefile["name"]
            if not os.path.exists(dest):
                print 'get sample file: '+samplefile["url"]
                urllib.urlretrieve(samplefile["url"], dest)
                unzip_file("tmp/sample/" + samplefile["name"], "tmp/unzip_sample/" + exp)
            else:
                print 'sample file exists'
            #setup_dataset(exp)
    return True

#setup data from file downloaded
def setup_dataset(exp):  
    path = 'tmp/unzip_sample/' + exp
    dir = os.listdir(path)
    dir.sort()
    for f in dir:
        #samplenames.append(f.split(".")[0].split("_")[0])
        file = open(path+'/'+f, 'r')
        line = file.readline().strip()
        first_line = True        
        while line != '':
            splited = line.split("\t")
            #check format, and skip first line
            if first_line:                    
                first_line = False
                line = file.readline().strip()
                continue
            #make sure data is digital
            #print splited
            for d in splited[1:]:
                try:
                    float(d)
                except ValueError, e:
                    print e
                    file.close()
                    return False
            reporter = splited[0]
            if reporter in data_matrix:
                data_matrix[reporter].extend(splited[1:])
            else:
                data_matrix[reporter] = splited[1:]
            line = file.readline().strip()
        file.close()
        #print data_matrix
    return True
            
#     while True:
#         biogpsdict = {}
#         i = 0
#         for file in files:
#             line = file.readline().strip()
#             print line,
#             splited = line.split("\t")
#             if len(splited) == 2:
#                 print 'WARNING: this file format might be different!'
#                 return False
#             if not line:
#                 break
#             biogpsdict[samplename[i]] = oneline[1].replace("\n", "")
#             i = i + 1
#         if not line:
#             for file in files:
#                 file.close()
#             break
#         if count > 0:
#             reporters.append(oneline[0])
#             biogpsDatasetData = models.BiogpsDatasetData(dataset=biogpsDataset, reporter=oneline[0], data=biogpsdict)
#             biogpsDatasetData.save()
#         count = count + 1
#     newplatform = models.BiogpsDatasetPlatform.objects.get(platform=name)
#     newplatform.reporters = reporters
#     newplatform.save()



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
