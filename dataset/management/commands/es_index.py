# -*-coding: utf-8 -*-
from dataset import models
from django.core.management.base import BaseCommand
import json
from django.conf import settings
import requests
from requests.exceptions import HTTPError


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            r = requests.delete(settings.ES_URLS['BGPS'])
            r.raise_for_status()
            print "delete biogps index success"
        except HTTPError:
            print "no existing biogps index, continue."
        except Exception, e:
            print e
            print 'clear exist biogps index failed, leave.'
            return

        requests.put(settings.ES_URLS['BGPS'])
        print 'create index for biogps success'

        data = json.dumps({
            "platform": {
                "properties": {
                    "platform": {"type": "string", "store": True},
                    "reporters": {"type": "string", "store": True}}}})
        requests.put(settings.ES_URLS['PF_C'], data=data)
        print "create platform mapping success"

        data = json.dumps({
            "dataset": {
                "_parent": {"type": "platform"},
                "properties": {
                    "default": {"type": "integer", "store": True},
                    "name": {"type": "string", "store": True},
                    "summary": {"type": "string", "store": True},
                    "geo_gse_id": {"type": "string", "store": True}}}})
        requests.put(settings.ES_URLS['DS_C'], data=data)
        print "create dataset mapping success"

        plt_body = {"platform": "", "reporters": ""}
        platform = models.BiogpsDatasetPlatform.objects.all()
        plt_count, bio_count = 0, 0
        for item in platform:
            plt_body["reporters"] = item.reporters
            plt_body["platform"] = item.platform
            data = json.dumps(plt_body)
            plt_url = settings.ES_URLS['PF'] + str(plt_count)
            requests.post(plt_url, data=data)
            plt_count = plt_count + 1
            # temp_data中的default字段表面了该document来自那个数据库，整数1表明来自默认数据库
            for ds in item.dataset_platform.all():
                temp_data = ds.es_index_serialize()
                temp_data["default"] = 0
                data = json.dumps(temp_data)
                url = settings.ES_URLS['DS'] + \
                    str(bio_count) + "?parent=" + str(plt_count - 1)
                requests.put(url, data=data)
                bio_count = bio_count + 1

        print "from 'default' database,added %d platform , added %d dataset" %\
            (plt_count, bio_count)

        dataset = models.BiogpsDataset.objects.using("default_ds").\
            filter(geo_gse_id__in=settings.DEFAULT_DS_ACCESSION)
        plt_ds, bio_ds = plt_count, bio_count

        plt_dic = {}
        for ds in dataset:
            plt_temp = ds.platform
            plt_body["reporters"] = plt_temp.reporters
            plt_body["platform"] = plt_temp.platform
            # plt_id用于保存插入dataset时对应的plt的id(esindex)
            plt_id = plt_count
            if plt_dic.get(str(plt_temp.id), None) is None:
                data = json.dumps(plt_body)
                plt_url = settings.ES_URLS['PF'] + str(plt_count)
                requests.post(plt_url, data=data)
                plt_count = plt_count + 1
                plt_dic[str(plt_temp.id)] = plt_id
            else:
                plt_id = plt_dic.get(str(plt_temp.id))

            # temp_data中的default字段表面了该document来自那个数据库，整数1表明来自数据库default_ds
            temp_data = ds.es_index_serialize()
            temp_data["default"] = 1
            data = json.dumps(temp_data)
            url = settings.ES_URLS['DS'] + \
                str(bio_count) + "?parent=" + str(plt_id)
            requests.put(url, data=data)
            bio_count = bio_count + 1
        print "from 'default_ds' database, added %d platform, added %d dataset"\
            % (plt_count - plt_ds, bio_count - bio_ds)
