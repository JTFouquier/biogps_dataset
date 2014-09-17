#-*-coding: utf-8 -*-                               
from dataset import models                          
from elasticsearch import  Elasticsearch            
from django.core.management.base import BaseCommand 

class Command(BaseCommand):             
    def handle(self, *args, **options): 
        ds_plat = models.BiogpsDatasetPlatform.objects.using("default_ds").all()
        for  plt_item in ds_plat:
            ds_sets = plt_item.dataset_platform
            plt_item.save(using = "default_dataset")
            for set_item in ds_sets:
                ds_datas = set_item.dataset_data
                set_item.save(using = "default_dataset")
                for data_item in ds_datas:
                    data_item.save(using = "default_dataset")