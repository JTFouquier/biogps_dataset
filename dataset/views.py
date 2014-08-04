#-*-coding: utf-8 -*-
import csv
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
    except Exception, e:
        ds = models.BiogpsDataset.objects.first()
    return ds
   
 #return an array of keys that stand for samples in ds   
def get_ds_factors_keys(ds):
    factors =[]
    for f in ds.metadata['factors']:
#        print f
        comment=f[f.keys()[0]]['comment']
        temp=comment.get('Sample_title',None)
        if temp==None:
            temp=comment.get('Sample_title',None)
            if temp == None:
                temp=f.keys()[0]
        factors.append(temp)
    
    return factors
 
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
    fa = get_ds_factors_keys(ds)
    for f in fa:
        factors.append({f:{"color_idx":31,  "order_idx":76, "title":f}})
    ret.update(preset)
    ret.update({'factors':factors})
    #print factors
    ret = json.dumps(ret)
    return HttpResponse('{"code":0, "detail":%s}'%ret, content_type="application/json")

def  get_dataset_data(_id):
    ds = adopt_dataset()
    url = 'http://mygene.info/v2/gene/%s/?fields=entrezgene,reporter,refseq.rna'%_id
    res = requests.get(url)
    data_json = res.json()
    reporters = []
    for i in data_json['reporter'].values():
        reporters = reporters+i
    dd = ds.dataset_data.filter(reporter__in = reporters)
    data_list = []
    for d in dd:
        data_list.append({d.reporter:{'values':d.data}})
    return {'id':ds.id, 'name':ds.name, 'data':data_list}

#显示柱状图，但是需要接受id和at参数
def dataset_chart(request,_id,reporter):
    if _id is None :
        return HttpResponse('{"code":4004, "detail":"argument needed"}', content_type="application/json")
    data_list=get_dataset_data(_id)['data']
    print "data_list==",data_list
    str_list=[]
    for item in data_list:
        if reporter  in item:
             str_list=item[reporter]["values"]
             break
    
    if  len(str_list)==0:
        return HttpResponse('{"code":4004, "detail":"reporter  can not  find"}', content_type="application/json")
    
    val_list=[]
    for item in str_list:
        temp=float(item)
        val_list.append(temp)
    
    ds = adopt_dataset()
    name_list=get_ds_factors_keys(ds)
    
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import matplotlib.pyplot as plt 
    import django
    import numpy as np
    #判断要画几根柱状图
    length=len(name_list)
    y_pos=[0,]
#    per=1.0/length
#    per_next=1.0/length*(1.0/8)
    i=1;
    while(i<length):
        y_pos.append(i)
        i=i+1
    
    plt.figure(1,figsize=(160,3+length*1.5),dpi=15).clear()
  
   #计算x轴的最大值  
    temp_count=0
    temp_val=0
    temp=np.median(val_list)
    x_max=30*temp
    x_max=int(x_max)
    print "xxxxx====",x_max,"    ==",temp
    while x_max>0:
        temp_count=temp_count+1
        temp_val=x_max%10
        x_max=x_max/10
    x_max=(temp_val+1)*10**(temp_count-1)
    
#修改背景色
    fig1 = plt.figure(1)
    rect=fig1.patch
    rect.set_facecolor('white')
#画柱状图    
    xylist=[0, 0, 0,]
    xylist.append(length+2)  
    xylist[1]=x_max  
    plt.axis(xylist)
    plt.barh(y_pos,val_list,height=1*7.0/8,color="m")
#画label 
    i=0
    for name_item in name_list :
        plt.text(0,y_pos[i],name_item,fontsize=80,horizontalalignment='right')
        i=i+1

#画x坐标    x位3,10,30程中位数
    x_median=np.median(val_list)
    x_per_list=[1,3,10,30]
    i=1
    y_list=[]
    y_list.append(length+0.2)
#    y_list.append(length-0.5)
    y_list.append(0)
    print x_max,'   ',x_median
    while i<=4:
        x_label=x_median*x_per_list[i-1]
#        if x_label>x_max:
#            print "x_label=",x_label,"    x_max=",x_max,"   i=",i
#            break
        str_temp='%.2f'%x_label
        print str_temp
        plt.text(x_label-0.3*x_max/30,length+0.5,str_temp,fontsize=80)
        #plt.text(x_label,length,str_temp,fontsize=80)
        list_temp=[]
        list_temp.append(x_label)
        list_temp.append(x_label)
        plt.plot(list_temp, y_list,"k",linewidth=4)
        i=i+1
    list_temp=[]
    list_temp.append(0)
    list_temp.append(x_max)
    y_list=[]
    y_list.append(length)
    y_list.append(length)
    plt.plot(list_temp, y_list,"k",linewidth=4)
    canvas = FigureCanvas(plt.figure(1))
    response=django.http.HttpResponse(content_type='image/png')
    canvas.print_png(response) 
    return response


#简单的返回查询的结果
from django.views.decorators.csrf import csrf_exempt
import json  
@csrf_exempt
def show_search(request):
    my_str=request.POST.get("str",None)
    body={"query" : {"match" : {"_all": " "}}}
    from elasticsearch import  Elasticsearch
    es=Elasticsearch()
    body["query"]["match"]["_all"]=my_str
    my_json=es.search(index="blogs",doc_type="biogps",body=body)
   # print "======================="
   # print my_json
    #print "======================="
    response = HttpResponse()
    response.status_code = 200
    response['Content-Type'] = "application/json"
    response.content = json.dumps(my_json)
    return response

def get_cvs(request):
     _id = request.GET.get('id', None)
     if _id is None:
         return HttpResponse('{"code":4004, "detail":"argument needed"}', content_type="application/json")
     data_list=get_dataset_data(_id)['data']
     row_list=['Tissue']
     val_list=[]
     for item in data_list:
         key_list=item.keys()
         for key_item in key_list:
             row_list.append(key_item)
             val_list.append(item[key_item]['values'])
     length=len(val_list[0])       
     ds = adopt_dataset()
     name_list=get_ds_factors_keys(ds)
     response = HttpResponse(mimetype='text/csv')
     response['Content-Disposition'] = 'attachment; filename=asd.csv'
     writer = csv.writer(response)
     writer.writerow(row_list)
     i=0
     while(i<length):
         temp_list=[]
         temp_list.append(name_list[i])
         for item in val_list:
             temp_list.append(item[i])
         writer.writerow(temp_list)
         i=i+1   
     return response
    
    
    
#get information about a dataset
@require_http_methods(["GET"])
def dataset_data(request):
    _id = request.GET.get('id', None)
    if _id is None :
        return HttpResponse('{"code":4004, "detail":"argument needed"}', content_type="application/json")
    ret = get_dataset_data(_id)
    print ret
    ret['probeset_list'] = ret['data']
    del ret['data']
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
