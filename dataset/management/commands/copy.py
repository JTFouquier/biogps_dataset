from dataset import models
from elasticsearch import  Elasticsearch
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    def handle(self, *args, **options):
        temp=models.BiogpsDataset.objects.all()
        es=Elasticsearch()
        i=0
        for item in temp:
            i=i+1
            es.index(index="blogs", doc_type="biogps", body={"name":item.name,"summary":item.summary,"id":item.id}, id=i)
        print "success!!"   