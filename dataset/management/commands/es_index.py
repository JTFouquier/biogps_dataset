# -*-coding: utf-8 -*-
from optparse import make_option
from dataset import models
from django.core.management.base import BaseCommand
import json
from django.conf import settings
import requests
from requests.exceptions import HTTPError


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option("-c", "--create-index",
                    action="store_true",
                    dest="create-index",
                    default=False,
                    help='Create new ES index, delete the old one if exists.'
        ),)

    def _create_es_index(self):
        '''Create the ES index, delete it first if exists'''
        try:
            r = requests.delete(settings.ES_URLS['BGPS'])
            r.raise_for_status()
            print("delete biogps index success")
        except HTTPError:
            print("no existing biogps index, continue.")
        except Exception as e:
            print(e)
            print('clear exist biogps index failed, leave.')
            return

        requests.put(settings.ES_URLS['BGPS'])
        print('create index for biogps success')

        data = json.dumps({
            "platform": {
                "properties": {
                    "platform": {"type": "string", "store": False, "include_in_all": False},
                    "reporters": {"type": "string", "store": False,
                                  'index': 'not_analyzed', "include_in_all": False},
                    "species": {"type": "string", "include_in_all": False}
                    }}})
        requests.put(settings.ES_URLS['PF_C'], data=data)
        print("create platform mapping success")

        data = json.dumps({
            "dataset": {
                "_parent": {"type": "platform"},
                "properties": {
                    "id": {"type": "integer"},
                    "is_default": {"type": "boolean"},
                    "name": {"type": "string"},
                    "slug": {"type": "string"},
                    "summary": {"type": "string"},
                    "geo_gse_id": {"type": "string"},
                    "factor_count": {"type": "integer"},
                    "sample_count": {"type": "integer"},
                    "species": {"type": "string"},
                    "tags": {"type": "string", "index": "not_analyzed"}
                    }}})
        requests.put(settings.ES_URLS['DS_C'], data=data)
        print("create dataset mapping success")

    def _index_datasets(self):
        '''Do the actual indexing on an existing ES index.'''
        plt_body = {"platform": "", "reporters": ""}
        platform = models.BiogpsDatasetPlatform.objects.all()
        plt_count, bio_count = 0, 0
        for item in platform:
            plt_body["reporters"] = item.reporters
            plt_body["platform"] = item.platform
            plt_body["species"] = item.species
            data = json.dumps(plt_body)
            plt_url = settings.ES_URLS['PF'] + str(plt_count)
            requests.post(plt_url, data=data)
            plt_count = plt_count + 1
            # temp_data中的default字段表面了该document来自那个数据库，整数1表明来自默认数据库
            for ds in item.dataset_platform.all():
                temp_data = ds.es_index_serialize()
                data = json.dumps(temp_data)
                url = settings.ES_URLS['DS'] + \
                    str(bio_count) + "?parent=" + str(plt_count - 1)
                requests.put(url, data=data)
                bio_count = bio_count + 1

        print("added {} platform , added {} dataset".format(plt_count, bio_count))

    def handle(self, *args, **options):
        if options['create-index']:
            self._create_es_index()
        self._index_datasets()


#
#         dataset = models.BiogpsDataset.objects.using("default_dataset").\
#             filter(geo_gse_id__in=settings.DEFAULT_DS_ACCESSION)
#         plt_ds, bio_ds = plt_count, bio_count
#
#         plt_dic = {}
#         for ds in dataset:
#             plt_temp = ds.platform
#             plt_body["reporters"] = plt_temp.reporters
#             plt_body["platform"] = plt_temp.platform
#             # plt_id用于保存插入dataset时对应的plt的id(esindex)
#             plt_id = plt_count
#             if plt_dic.get(str(plt_temp.id), None) is None:
#                 data = json.dumps(plt_body)
#                 plt_url = settings.ES_URLS['PF'] + str(plt_count)
#                 requests.post(plt_url, data=data)
#                 plt_count = plt_count + 1
#                 plt_dic[str(plt_temp.id)] = plt_id
#             else:
#                 plt_id = plt_dic.get(str(plt_temp.id))
#
#             # temp_data中的default字段表面了该document来自那个数据库，整数1表明来自数据库default_ds
#             temp_data = ds.es_index_serialize()
#             temp_data["default"] = 1
#             data = json.dumps(temp_data)
#             url = settings.ES_URLS['DS'] + \
#                 str(bio_count) + "?parent=" + str(plt_id)
#             requests.put(url, data=data)
#             bio_count = bio_count + 1
#         print "from 'default_dataset' database, added %d platform, added %d dataset"\
#             % (plt_count - plt_ds, blio_count - bio_ds)
