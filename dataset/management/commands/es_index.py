from dataset import models
from elasticsearch import  Elasticsearch
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        qs = models.BiogpsDataset.objects.all()
        es = Elasticsearch()
        for item in qs:
            es.delete(index="blogs", doc_type="biogps", id=item.id)
            es.index(index="blogs", doc_type="biogps",  \
                    body=item.es_index_serialize(), id=item.id)
        print "%d datasets added to ES." % qs.count()
