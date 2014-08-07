from dataset import models
from elasticsearch import  Elasticsearch
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        qs = models.BiogpsDataset.objects.all()
        es = Elasticsearch()
        for item in qs:
            es.index(index="blogs", doc_type="biogps", body=item.get_body(), \
                     id=item.id)
        print "%d datasets added to ES." % qs.count()
