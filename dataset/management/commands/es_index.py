from dataset import models
from elasticsearch import  Elasticsearch
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
                "reporters": {"type": "string", "store": True},
                "id": {"type": "string", "store": True}}}})
        requests.put(settings.ES_URLS['PF_C'], data=data)
        print "create platform mapping success"

        data = json.dumps({
        "dataset": {
        "_parent": {"type": "platform"},
            "properties": {
                "name": {"type": "string", "store": True},
                 "summary": {"type": "string", "store": True},
                  "id": {"type": "string", "store": True}}}})
        requests.put(settings.ES_URLS['DS_C'], data=data)
        print "create dataset mapping success"

        plt_body = {"platform": "", "reporters": "", "id": ""}
        platform = models.BiogpsDatasetPlatform.objects.all()
        plt_count, bio_count = 0, 0
        for item in platform:
            plt_body["id"] = str(item.id)
            plt_body["reporters"] = item.reporters
            plt_body["platform"] = item.platform
            data = json.dumps(plt_body)
            plt_url = settings.ES_URLS['PF'] + str(item.id)
            requests.post(plt_url, data=data)
            plt_count = plt_count + 1
            for ds in item.dataset_platform.all():
                data = json.dumps(ds.es_index_serialize())
                url = settings.ES_URLS['DS'] + \
                    str(ds.id) + "?parent=" + plt_body["id"]
                requests.put(url, data=data)
                bio_count = bio_count + 1

        print "added %d platform , added %d dataset" % (plt_count, bio_count)
