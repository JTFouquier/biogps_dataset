from dataset import models
from elasticsearch import  Elasticsearch
from django.core.management.base import BaseCommand
import urllib2
import json


class Command(BaseCommand):
    def handle(self, *args, **options):
        request = urllib2.Request(r"http://localhost:9200/blogs/platform")
        request.get_method = lambda: 'DELETE'
        urllib2.urlopen(request)
        print "del platform success"

        data = json.dumps({
        "platform": {
            "properties": {
                "platform": {"type": "string", "store": True},
                "reporters": {"type": "string", "store": True},
                "id": {"type": "string", "store": True}}}})
        request = urllib2.Request(\
                r"http://localhost:9200/blogs/platform/_mapping",\
                data=data)
        request.get_method = lambda: 'PUT'
        urllib2.urlopen(request)
        print "create platform success"

        request = urllib2.Request(r"http://localhost:9200/blogs/dataset/")
        request.get_method = lambda: 'DELETE'
        urllib2.urlopen(request)
        print "delete dataset success"

        data = json.dumps({
        "dataset": {
        "_parent": {"type": "platform"},
            "properties": {
                "name": {"type": "string", "store": True},
                 "summary": {"type": "string", "store": True},
                  "id": {"type": "string", "store": True}}}})
        url = "http://localhost:9200/blogs/dataset/_mapping"
        request = urllib2.Request(url, data=data)
        request.get_method = lambda: 'PUT'
        urllib2.urlopen(request)

        plt_body = {"platform": "", "reporters": "", "id": ""}

        platform = models.BiogpsDatasetPlatform.objects.all()
        plt_count, bio_count = 0, 0
        for item in platform:
            plt_body["id"] = str(item.id)
            plt_body["reporters"] = item.reporters
            plt_body["platform"] = item.platform
            data = json.dumps(plt_body)

            plt_url = r"http://localhost:9200/blogs/platform/" + str(item.id)
            request = urllib2.Request(plt_url, data=data)
            request.get_method = lambda: 'post'
            urllib2.urlopen(request)
            plt_count = plt_count + 1
            for bio_item in item.dataset_platform.all():
                bio_body = bio_item.es_index_serialize()
                date = json.dumps(bio_body)

                bio_url = r"http://localhost:9200/blogs/dataset/" + \
                str(bio_item.id) + "?parent=" + plt_body["id"]
                request = urllib2.Request(bio_url, data=date)
                request.get_method = lambda: 'PUT'
                request.add_header('User-Agent', 'fake-client')
                urllib2.urlopen(request)
                bio_count = bio_count + 1

        print "add %d platform , add %d dataset" % (plt_count, bio_count)
