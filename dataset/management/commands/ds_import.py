# -*-coding: utf-8 -*-

from dataset import models
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        print 'remove existing data'
        models.BiogpsDatasetPlatform.objects.\
            using("default_dataset").all().delete()

        ds_set = models.BiogpsDataset.objects.using("default_ds").\
            filter(id__in=settings.DEFAULT_DS_ID)
        print 'write new data'
        platforms = []
        for ds in ds_set:
            plt = ds.platform
            if plt.id in platforms:
                pass
            else:
                platforms.append(plt.id)
                plt.save(using="default_dataset")
            ds.save(using="default_dataset")
            ds_datas = ds.dataset_data.all()
            for data_item in ds_datas:
                data_item.save(using="default_dataset")
        print "done"
