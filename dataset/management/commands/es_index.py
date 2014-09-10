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
            r = requests.delete(settings.ES_BIOGPS)
            r.raise_for_status()
            print "delete biogps index success"
        except HTTPError:
            print "no existing biogps index, continue."
        except Exception, e:
            print e
            print 'clear exist biogps index failed, leave.'
            return

      #  request = urllib.request.Request(\
      #          r"http://localhost:9200/biogps/", method='PUT')
      #  urllib.urlopen(request)
        requests.put(settings.ES_BIOGPS)
        print 'create index for biogps success'

        data = json.dumps({
        "platform": {
            "properties": {
                "platform": {"type": "string", "store": True},
                "reporters": {"type": "string", "store": True},
                "id": {"type": "string", "store": True}}}})
        #request = urllib.request.Request(settings.ES_URL, \
        #                                 data=data, method='PUT')
        #urllib.urlopen(request)
        requests.put(settings.ES_URL, data=data)
        print "create platform mapping success"

        data = json.dumps({
        "dataset": {
        "_parent": {"type": "platform"},
            "properties": {
                "name": {"type": "string", "store": True},
                 "summary": {"type": "string", "store": True},
                  "id": {"type": "string", "store": True}}}})
        #request = urllib.request.Request(settings.ES_URL, data=data, method='PUT')
        #urllib.urlopen(request)
        requests.put(settings.ES_URL, data=data)
        print "create dataset mapping success"

        plt_body = {"platform": "", "reporters": "", "id": ""}
        platform = models.BiogpsDatasetPlatform.objects.all()
        plt_count, bio_count = 0, 0
        for item in platform:
            plt_body["id"] = str(item.id)
            plt_body["reporters"] = item.reporters
            plt_body["platform"] = item.platform
            data = json.dumps(plt_body)
            plt_url = settings.ES_PLAT + str(item.id)
            #request = urllib.request.Request(plt_url, data=data, method='POST')
            #urllib.urlopen(request)
            requests.post(plt_url, data=data)
            plt_count = plt_count + 1
            for bio_item in item.dataset_platform.all():
                bio_body = bio_item.es_index_serialize()
                date = json.dumps(bio_body)
                bio_url = settings.ES_DATASET + \
                str(bio_item.id) + "?parent=" + plt_body["id"]
                #request = urllib.request.Request(bio_url, data=date, method='PUT')
                #urllib.urlopen(request)
                requests.put(bio_url, data=data)
                bio_count = bio_count + 1

        print "add %d platform , add %d dataset" % (plt_count, bio_count)
