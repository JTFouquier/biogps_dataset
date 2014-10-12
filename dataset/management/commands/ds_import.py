#-*-coding: utf-8 -*-                               
from dataset import models                          
from elasticsearch import  Elasticsearch            
from django.core.management.base import BaseCommand
from django.conf import settings 

class Command(BaseCommand):
    def handle(self, *args, **options):
        print 'remove existing data'
        models.BiogpsDatasetPlatform.objects.\
            using("default_dataset").all().delete()

        ds_set = models.BiogpsDataset.objects.using("default_ds").\
        filter(id__in = settings.DEFAULT_DS_ID)
        print 'write new data'
        for set_item in ds_set:
            ds_plt = set_item.platform
            if ds_plt.id in plt_dic :
                pass
            else:
                plt_dic.append(ds_plt.id)
                ds_plt.save(using = "default_dataset")

            set_item.save(using = "default_dataset")

            ds_datas =  set_item.dataset_data.all()
            for data_item in ds_datas:
                data_item.save(using = "default_dataset")
            
        print "done"
