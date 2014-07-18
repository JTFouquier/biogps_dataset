from django.conf import settings
from django.views.decorators.http import require_http_methods
import models
from django.http.response import HttpResponse
import json
import datetime
from django.db.models.query import QuerySet
from django.core.serializers import serialize, deserialize
from json.encoder import JSONEncoder
from django.db.models.base import Model
import requests

def adopt_dataset():
    try:
        ds_id = settings.DEFAULT_DATASET_ID
        ds = models.BiogpsDataset.objects.get(id=ds_id)
    except Exception:
        ds = models.BiogpsDataset.objects.first()
    return ds
    
    
#get information about a dataset
@require_http_methods(["GET"])
def dataset_info(request):
    ds = adopt_dataset()
    preset = {'default':True, 'permission_style':'public', 'role_permission': ['biogpsusers'], 'rating_data':{ 'total':5, 'avg_stars':10, 'avg':5 }, 
        'display_params': {'color': ['color_idx'], 'sort': ['order_idx'], 'aggregate': ['title']}
     }
    ret = {'id':ds.id, 'name_wrapped':ds.name, 'name':ds.name, 'owner': ds.ownerprofile_id, 'lastmodified':ds.lastmodified.strftime('%Y-%m-%d %H:%M:%S'), 
           'pubmed_id':ds.metadata['pubmed_id'], 'summary':ds.summary, 'geo_gse_id':ds.geo_gse_id, 'created':ds.created.strftime('%Y-%m-%d %H:%M:%S'),
            'geo_gpl_id':ds.metadata['geo_gpl_id']['accession'], 'species':[ds.species] 
    }
    factors = []
    for f in ds.metadata['factors']:
        k = f.keys()[0]
        factors.append({k:{"color_idx":31,  "order_idx":76, "title":k}})
    ret.update(preset)
    ret.update({'factors':factors})
    #print factors
    ret = json.dumps(ret)
    return HttpResponse('{"code":0, "detail":%s}'%ret, content_type="application/json")

#get information about a dataset
@require_http_methods(["GET"])
def dataset_data(request):
    _id = request.GET.get('id', None)
    if _id is None:
        return HttpResponse('{"code":4004, "detail":"argument needed"}', content_type="application/json")
    ds = adopt_dataset()
    url = 'http://mygene.info/v2/gene/%s/?fields=entrezgene,reporter,refseq.rna'%_id
    res = requests.get(url)
    data_json = res.json()
    reporters = []
    for i in data_json['reporter'].values():
        reporters = reporters+i
    dd = ds.dataset_data.filter(reporter__in = reporters)
    ret = {'id':ds.id, 'name':ds.name}
    data_list = []
    for d in dd:
        data_list.append({d.reporter:{'values':d.data}})
    ret['probeset_list'] = data_list
    return HttpResponse('{"code":0, "detail":%s}'%json.dumps(ret), content_type="application/json")
    
    
class ComplexEncoder(JSONEncoder):
    def default(self, obj):
        print type(obj)
        if isinstance(obj, Model):
            return json.loads(serialize('json', [obj])[1:-1])['fields']
        if isinstance(obj, QuerySet):
            obj = obj.values()
            obj = list(obj)
            return json.loads(json.dumps(obj, cls=ComplexEncoder))
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M')
        if isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

    def jsonBack(self, json):
        if json[0] == '[':
            return deserialize('json', json)
        else:
            return deserialize('json', '[' + json + ']')
