from django.core.management.base import BaseCommand
import urllib
import urllib2
import json
import os
import sys
import os.path
import zipfile
from dataset import models


class Command(BaseCommand):
    def handle(self, *args, **options):
        f = open('jsonexp.txt', 'wb')
        f.close()
