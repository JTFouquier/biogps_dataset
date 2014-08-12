import logging
import os
import requests
import requests_cache
import zipfile
import csv
import StringIO
import json
from dataset import models


class ResourceRequest:
    @staticmethod
    def get(url):
        response = requests.get(url)
        if response.status_code != 200:
            raise Exception('can not load url %s' % url)
        return response


class Platform(ResourceRequest):

    def __init__(self, name):
        self.name = name
        self.reports = None
        self.exps = None
        #save as biogps plstform
        self.platform = None

    def load(self):
        self.load_reporters()
        self.load_exps()

    def load_reporters(self):
        url = 'http://www.ebi.ac.uk/arrayexpress/files/%s/%s.adf.txt'\
            % (self.name, self.name)
        response = ResourceRequest.get(url)
        raw = response.content.strip()
        split = raw.split('\n')
        start = split.index('[main]') + 2
        split = split[start:]
        self.reporters = []
        for s in split:
            self.reporters.append(s.strip().split('\t')[0])
        self.reporters.sort()

    def load_exps(self):
        url = "http://www.ebi.ac.uk/arrayexpress/json/v2/files?array="\
             + self.name
        data_json = requests.get(url).json()
        if data_json["files"]["total-experiments"] > 0:
            self.exps = []
            experiments = data_json["files"]["experiment"]
            for experiment in experiments:
                accession = experiment["accession"]
                self.exps.append(accession)
            self.exps.sort()

    def save(self):
        self.platform, created = models.BiogpsDatasetPlatform.objects.\
          get_or_create(platform=self.name, reporters=self.reporters)


class ExperimentRaw(ResourceRequest):
    """
        read specified experiment and parse data
    """
    URL = "http://www.ebi.ac.uk/arrayexpress/json/v2/"

    def __init__(self, name):
        '''
            dump -- an existing path to dump downloaded file, say,
                for human reading.
        '''
        self.name = name
        #exp desc, json
        self.info = None
        #sdrf, processed file urls and others
        self.files_info = None
        #sdrf file content as StringIO
        self.sdrf = None
        #processed data file name and
        #file content mapping
        self.data = None

    def get_json_by_url(self, url):
        res = ResourceRequest.get(url)
        return res.json()

    def get_stringio_by_url(self, url):
        raw = StringIO.StringIO()
        response = ResourceRequest.get(url)
        raw.write(response.content)
        return raw

    #unzip stringio to stringio
    def unzip_file(self, zfile):
        zobj = zipfile.ZipFile(zfile)
        ret = {}
        for name in zobj.namelist():
            output = StringIO.StringIO()
            output.write(zobj.read(name))
            ret[name] = output
        return ret

    def load_info(self):
        url = ExperimentRaw.URL + "experiments/" + self.name
        self.info = self.get_json_by_url(url)

    def load_files_info(self):
        url = ExperimentRaw.URL + "files/" + self.name
        data = self.get_json_by_url(url)
        if type(data["files"]["experiment"]) == list:
            for e in data["files"]["experiment"]:
                if e["accession"] == self.name:
                    self.files_info = e["file"]
        else:
            self.files_info = data["files"]["experiment"]["file"]

    def load_sdrf(self):
        logging.info('load_sdrf')
        for f in self.files_info:
            if f["kind"] == 'sdrf':
                self.sdrf = self.get_stringio_by_url(f["url"])
                break

    def load_processed_data(self):
        logging.info('load_processed_data')
        raw = None
        for f in self.files_info:
            if f["kind"] == 'processed':
                raw = self.get_stringio_by_url(f["url"])
                break
        if raw is not None:
            self.data_raw = self.unzip_file(raw)

    def load(self):
        self.load_info()
        self.load_files_info()
        self.load_sdrf()
        self.load_processed_data()

    #dump data to a folder named after exp name
    def dump(self):
        try:
            os.stat(self.name)
        except:
            os.mkdir(self.name)
        with open('%s/%s.sdrf' % (self.name, self.name), 'w') as f:
            f.write(self.sdrf.getvalue())
#         with open('%s/%s.sdrf.json' % (self.name, self.name), 'w') as f:
#             f.write(json.dumps(self.sdrf))
        
        for k in self.data_raw:
            with open('%s/%s' % (self.name, k), 'w') as f:
                f.write(self.data_raw[k].getvalue())
