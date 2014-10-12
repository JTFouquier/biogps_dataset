#-*-coding: utf-8 -*-
import csv
from django.conf import settings
from django.views.decorators.http import require_http_methods
import models
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
from elasticsearch import Elasticsearch
import math
from dataset.util import general_json_response, GENERAL_ERRORS
import StringIO
import mygene
import urllib2


def adopt_dataset(ds_id):
    #TODO: use geo_gse_id latter, , id__in=settings.DEFAULT_DS_ID
    if ds_id in settings.DEFAULT_DS_ID:
        return models.BiogpsDataset.objects.using('default_dataset')\
            .get(id=ds_id)
    try:
        return models.BiogpsDataset.objects.get(id=ds_id)
    except Exception:
        return None


#return an array of keys that stand for samples in ds
def get_ds_factors_keys(ds):
    factors = []
    i = 1
    for f in ds.metadata['factors']:
        order_idx = color_idx = None
        if 'comment' in f[f.keys()[0]]:
            comment = f[f.keys()[0]]['comment']
            temp = comment.get('Sample_title', None)
            if temp == None:
                temp = comment.get('Sample_title', None)
                if temp == None:
                    temp = f.keys()[0]
        else: #default ds here
            temp = f.keys()[0]
            content = f[temp]
            if 'order_idx' in content and 'color_idx' in content:
                order_idx = content['order_idx']
                color_idx = content['color_idx']
        if order_idx is None:
            item = {'name': temp, 'order_idx': i, 'color_idx': i}
            i = i + 1
        else:
            item = {'name': temp, 'order_idx': order_idx, 'color_idx': color_idx} 
        factors.append(item)
    return factors


#get information about a dataset
@require_http_methods(["GET"])
def dataset_info(request, ds_id):
    ds = adopt_dataset(ds_id)
    if ds is None:
        return HttpResponse('{"code":4004, "detail":"dataset with this id not \
            found"}', content_type="application/json")
    preset = {'default': True, 'permission_style': 'public', \
              'role_permission': ['biogpsusers'], 'rating_data':\
              {'total': 5, 'avg_stars': 10, 'avg': 5}, 'display_params':\
             {'color': ['color_idx'], 'sort': ['order_idx'], 'aggregate': \
              ['title']}
     }
    if type(ds.metadata['geo_gpl_id']) is dict:
        geo_gpl_id = ds.metadata['geo_gpl_id']['accession']
    else:
        geo_gpl_id = ds.metadata['geo_gpl_id']
    ret = {'id': ds.id, 'name_wrapped': ds.name, 'name': ds.name, \
           'owner': ds.ownerprofile_id, 'lastmodified':\
           ds.lastmodified.strftime('%Y-%m-%d %H:%M:%S'),\
           'pubmed_id': ds.metadata['pubmed_id'], 'summary': ds.summary,\
           'geo_gse_id': ds.geo_gse_id, 'created':\
           ds.created.strftime('%Y-%m-%d %H:%M:%S'),\
           'geo_gpl_id': geo_gpl_id, 'species': [ds.species]
    }
    factors = []
    fa = get_ds_factors_keys(ds)
    for f in fa:
        factors.append({f['name']: {"color_idx": f.get('color_idx', 0),  \
            "order_idx": f.get('order_idx', 0), "title": f['name']}})
    ret.update(preset)
    ret.update({'factors': factors})
    #print factors
    ret = json.dumps(ret)
    return HttpResponse('{"code":0, "detail":%s}' % ret, \
                        content_type="application/json")


def _get_reporter_from_gene(gene):
    mg = mygene.MyGeneInfo()
    #res = mg.querymany([gene], scopes='_id', fields='reporter')
    data_json = mg.getgene(gene,fields='reporter')
    if 'reporter' not in data_json:
        return None
    reporters = []
    for i in data_json['reporter'].values():
        if type(i) is not list:
            i = [i]
        reporters = reporters + i
    return reporters


def  get_dataset_data(ds, gene_id=None, reporter_id=None):
    reporters = []
    if gene_id is not None:
        reporters = _get_reporter_from_gene(gene_id)
    elif reporter_id is not None:
        reporters.append(reporter_id)
    else:
        return None
    dd = ds.dataset_data.filter(reporter__in=reporters)
    data_list = []
    for d in dd:
        data_list.append({d.reporter: {'values': d.data}})
    return {'id': ds.id, 'name': ds.name, 'data': data_list}

def chart_data(val_list, factors):
    #back_dic存储返回结果的list
    back_dic = {}
    #存储要返回的val的值
    temp_val = []
    #存储要返回的name
    temp_name = []
    #存储要返回的标准差的值
    dev_list = []
    i = 0
    #遍历list，合并order值相同的字段
    while i < len(val_list):
        order_idx = factors[i]["order_idx"]
        name = factors[i]["name"].split('.')[0]
        count = 0
        total = 0
        temp_dev = []
        #查找order相同的元素，求值的和，和个数，并把每一个值放入temp_dev中
        while  i < len(val_list) and factors[i]["order_idx"] == order_idx:
            count = count + 1
            total = total + val_list[i]
            temp_dev.append(val_list[i])
            i = i + 1
        #根据和求平均值
        average = round(float(total) / count, 2)
        temp_val.append(average)
        temp_name.append(name)
        #判断,当只有一个元素的时候,标准差直接为0
        total = 0
        if count == 1:
            dev_list.append(0)
        else:
            #否则，先求每个元素与平均数的差的平方的和
            for j in temp_dev:
                total = total + (j - average) ** 2
            dev_list.append(round(math.sqrt(float(total) / count), 3))
    back_dic["val_list"] = temp_val
    back_dic["name_list"] = temp_name
    back_dic["deviation"] = dev_list
    return back_dic

#显示柱状图，但是需要接受id和at参数
def dataset_chart(request, ds_id, reporter_id):
    ds = adopt_dataset(ds_id)
    if ds is None:
        return HttpResponse('{"code":4004, "detail":"dataset with this id not \
            found"}', content_type="application/json")
    data_list = get_dataset_data(ds, reporter_id=reporter_id)['data']
    data_list = data_list[0][reporter_id]['values']
    val_list = []
    for item in data_list:
        temp = float(item)
        val_list.append(temp)
    factors = get_ds_factors_keys(ds)
    #name_list = [obj['name'] for obj in factors]

    back = chart_data(val_list, factors)
    val_list = back["val_list"]
    name_list = back["name_list"]
    devi_list = back["deviation"]

    val_list.reverse()
    name_list.reverse()
    devi_list.reverse()

    label_maxlen = 0
    for item in name_list:
        if len(item) > label_maxlen:
            label_maxlen = len(item)

    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    import matplotlib.pyplot as plt
    import numpy as np
    #判断要画几根柱状图
    length = len(name_list)
    y_pos = [0]
    i = 1
    #由于后面设置上下的间距是０，所有在下面多画一个ｂａｒ，保证图片下面的留白
    while(i < length + 1):
        y_pos.append(i)
        i = i + 1

    #plt.figure(1, figsize=(80, (3+length * 1.5) / 2), dpi=15).clear()

    fig = plt.gcf()
    fig.clear()
    fig.set_dpi(15)
    fig.set_size_inches(80, (3 + length * 1.5) / 2)

    #计算x轴的最大值
    temp_count = 0
    temp_val = 0
    #先算出val_list的最大值
    x_max = 0
    for item in val_list:
        if x_max < item:
            x_max = item
    #由于x_max原先是float，需要转成int放弃小数
    x_max = int(x_max)
    while x_max > 0:
        temp_count = temp_count + 1
        temp_val = x_max % 10
        x_max = x_max / 10
    if temp_count != 1:
        x_max = int((temp_val + 1) * (10 ** (temp_count - 1)))
    else:
        x_max = 10

    #修改背景色
    fig1 = plt.figure(1)
    rect = fig1.patch
    rect.set_facecolor('white')

    #画柱状图
    xylist = [0, 0, 0]
    xylist.append(length + 2)
    xylist[1] = x_max
    plt.axis(xylist)
#多画一个为ｏ的ｂａｒ
    val_list = [0] + val_list
    plt.barh(y_pos, val_list, height=1 * 7.0 / 8,\
             color="m")
    #取消x轴和y轴
    plt.axis('off')
    #画label
    i = 1
    for name_item in name_list:
        mystr = "%s-" % name_item
        plt.text(0, y_pos[i], mystr, fontsize=40,\
                 horizontalalignment='right')
        i = i + 1

#画标准差
    i = 1
    for j in devi_list:
        if j - 0 > 0.001:
            list_x = [val_list[i], val_list[i] + j]
            list_y = [y_pos[i] + 0.5, y_pos[i] + 0.5]
            plt.plot(list_x, list_y, "k", linewidth=4)
            list_x = [val_list[i] + j, val_list[i] + j]
            list_y = [y_pos[i] + 0.2, y_pos[i] + 0.8]
            plt.plot(list_x, list_y, "k", linewidth=4)
        i = i + 1

    #画x坐标    x位3,10,30程中位数
    x_median = np.median(val_list)
    x_per_list = [1, 3, 10, 30]
    i = 1
    y_list = []
    y_list.append(length + 1 + 0.2)
    y_list.append(1)

    while i <= 4:
        x_label = x_median * x_per_list[i - 1]
        str_temp = '%.2f' % x_label
        if x_label < x_max:
            if i == 1:
                temp_text = "median(" + str_temp + ")"
            else:
                temp_text = "%dM(" + str_temp + ")"
                temp_text = temp_text % x_per_list[i - 1]
            plt.text(x_label - 0.5 * x_max / 30, 0.1,\
                     temp_text, fontsize=40)
        #plt.text(x_label,length,str_temp,fontsize=80)
        list_temp = []
        list_temp.append(x_label)
        list_temp.append(x_label)
        plt.plot(list_temp, y_list, "k", linewidth=4)
        i = i + 1
    #画框
    list_temp = []
    list_temp.append(0)
    list_temp.append(x_max)
    y_list = []
    y_list.append(length + 1)
    y_list.append(length + 1)
    plt.plot(list_temp, y_list, "k", linewidth=4)
    y_list[0] = 1
    y_list[1] = 1
    plt.plot(list_temp, y_list, "k", linewidth=4)

    list_temp[0] = x_max
    list_temp[1] = x_max
    y_list[0] = 1
    y_list[1] = length + 1
    plt.plot(list_temp, y_list, "k", linewidth=10)

    #画x轴
    y_list[0] = length + 1
    y_list[1] = length + 1 - 0.5
#要画的刻度
    i_range = []
    if x_max == 10:
        i_range = range(0, 11)
    else:
        i_range = range(0, temp_val + 2)
    for i in i_range:
        list_x = []
        x_val = i * (10 ** (temp_count - 1))
        list_x.append(x_val)
        list_x.append(x_val)
        plt.plot(list_x, y_list, "k", linewidth=3)

        plt.text(x_val - 0.3 * x_max / 30, length + 1 + 0.1,\
                 x_val, fontsize=40)
    #设置图形和图片左右的距离
    plt.subplots_adjust(left=0.05 * (label_maxlen + 5) / 10, right=0.9,\
                        top=1, bottom=0)

    #返回图片
    canvas = FigureCanvas(plt.figure(1))
    response = HttpResponse(content_type='image/png')
    canvas.print_png(response)
    return response


#filter by "default" field and "platform" and query by keywords
#if specified
def _es_search(rpt, q=None, dft=0, start=0, size=8):
    body = {"from": start, "size": size}
    #setup filter, filter is faster that query
    body['query'] = {"filtered": {"filter":{ "bool":{
        "must":[{"term":{"default":dft}},
                {"has_parent": {"parent_type": "platform","query": 
                {"match": {"reporters": rpt}}}}] }}
    }}
    #set query if query word is not None
    if q is not None:
        body["query"]["filtered"]["query"] = {"multi_match":{"query": q, 
            "fields": [ "summary", "name" ] }}

    data = json.dumps(body)
    r = requests.post(settings.ES_URLS['SCH'], data=data)
    return r.json()


#接受查询的字段组合query和获取的第几页page
@csrf_exempt
def dataset_search(request):
    query = request.GET.get("query", None)
    gene = request.GET.get("gene", None)
    page = request.GET.get("page", 1)
    page_by = request.GET.get("page_by", 8)

    if gene is None:
        gene = settings.DEFAULT_GENE_ID
    reporters = _get_reporter_from_gene(gene)
    if reporters is None:
        return general_json_response(code=GENERAL_ERRORS.ERROR_NOT_FOUND,\
                         detail='no matched data for gene %s.' % gene)
    page = int(page)
    page_by = int(page_by)
    rep = ' '.join(reporters)
    search_res = _es_search(rep, query, 0, (page-1)*page_by, page_by)
    count = search_res["hits"]["total"]

    total_page = int(math.ceil(float(count) / float(page_by)))
    res = []
    ids = []
    for item in search_res["hits"]["hits"]:
        ids.append(item["_source"]["geo_gse_id"])
    print ids
    ds_query = models.BiogpsDataset.objects.filter(geo_gse_id__in=ids)
    for ds_item in ds_query:
        temp_dic = {"id": ds_item.id, "name": ds_item.name}
        factors = get_ds_factors_keys(ds_item)
        temp_dic["factors"] = [obj['name'] for obj in factors]
        res.append(temp_dic)

    res = {"current_page": page, "total_page": total_page, "count": count,\
            "results": res}
    return general_json_response(detail=res)


@csrf_exempt
def dataset_search_default(request):
    query = request.GET.get("query", None)
    gene = request.GET.get("gene", None)
    if gene is None:
        gene = settings.DEFAULT_GENE_ID
    reporters = _get_reporter_from_gene(gene)
    if reporters is None:
        return general_json_response(code=GENERAL_ERRORS.ERROR_NOT_FOUND,\
                         detail='no matched data for gene %s.' % gene)
    #retrive all results
    search_res = _es_search(' '.join(reporters), query, 1, 0, 9999)
    ids = [item["_source"]["geo_gse_id"] for item in search_res["hits"]["hits"]]
    qs = models.BiogpsDataset.objects.using('default_ds')\
            .filter(geo_gse_id__in=ids)
    res = []
    for ds in qs:
        temp_dic = {"id": ds.id, "name": ds.name}
        factors = get_ds_factors_keys(ds)
        temp_dic["factors"] = [obj['name'] for obj in factors]
        res.append(temp_dic)
    res = {"count": qs.count(),   "results": res}
    return general_json_response(detail=res)


def dataset_csv(request, ds_id, gene_id):
    ds = adopt_dataset(ds_id)
    if ds is None:
        return HttpResponse('{"code":4004, "detail":"dataset with this id not \
            found"}', content_type="application/json")
    data_list = get_dataset_data(ds, gene_id=gene_id)['data']
    row_list = ['Tissue']
    val_list = []
    for item in data_list:
        key_list = item.keys()
        for key_item in key_list:
            row_list.append(key_item)
            val_list.append(item[key_item]['values'])
    length = len(val_list[0])
    name_list = get_ds_factors_keys(ds)
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s.csv' \
        % ds.geo_gse_id
    writer = csv.writer(response)
    writer.writerow(row_list)
    i = 0
    while(i < length):
        temp_list = []
        temp_list.append(name_list[i])
        for item in val_list:
            temp_list.append(item[i])
        writer.writerow(temp_list)
        i = i + 1
    return response


#get information about a dataset
@require_http_methods(["GET"])
def dataset_data(request, ds_id, gene_id):
    ds = adopt_dataset(ds_id)
    if ds is None:
        return HttpResponse('{"code":4004, "detail":"dataset with this id not \
            found"}', content_type="application/json")
    ret = get_dataset_data(ds, gene_id=gene_id)
    ret['probeset_list'] = ret['data']
    del ret['data']
    return HttpResponse('{"code":0, "detail":%s}' % json.dumps(ret), \
                        content_type="application/json")


def dataset_default(request):
    gene_id = request.GET.get('gene', None)
    if gene_id is None:
        gene_id = settings.DEFAULT_GENE_ID
    mg = mygene.MyGeneInfo()
    res = mg.querymany([gene_id], scopes='_id', fields='taxid')
    data_json = res[0]
    species = data_json['taxid']
    try:
        ds_id = settings.DEFAULT_DATASET_MAPPING[species]
    except:
        return general_json_response(GENERAL_ERRORS.ERROR_INTERNAL, \
                    "Cannot get default dataset with gene id: %s." % gene_id)
    return general_json_response(detail={'gene': int(gene_id), \
                                         'dataset': ds_id})


def dataset_correlation(request, ds_id, reporter_id, min_corr):
    """Return NumPy correlation matrix for provided ID, reporter,
       and correlation coefficient
    """
    import numpy as np

    def pearsonr(v, m):
        # Pearson correlation calculation taken from NumPy's implementation
        v_m = v.mean()
        m_m = m.mean(axis=1)
        r_num = ((v - v_m) * (m.transpose() - m_m).transpose()).sum(axis=1)
        r_den = np.sqrt(((v - v_m) ** 2).sum() *
            (((m.transpose() - m_m).transpose()) ** 2).sum(axis=1))
        r = r_num / r_den
        return r

    # Reconstruct dataset matrix
    ds = adopt_dataset(ds_id)
    try:
        _matrix = models.BiogpsDatasetMatrix.objects.get(dataset=ds)
    except models.BiogpsDatasetMatrix.DoesNotExist:
        return general_json_response(GENERAL_ERRORS.ERROR_NOT_FOUND, \
                    "Cannot get matrix of dataset: %s." % ds_id)
    reporters = _matrix.reporters

    # Get position of reporter
    if reporter_id in reporters:
        rep_pos = reporters.index(reporter_id)
        # Pearson correlations for provided reporter
        matrix_data = np.load(StringIO.StringIO(_matrix.matrix))
        rep_vector = matrix_data[rep_pos]
        corrs = pearsonr(rep_vector, matrix_data)
        # Get indices of sufficiently correlated reporters
        min_corr = float(min_corr)
        idx_corrs = np.where(corrs > min_corr)[0]
        # Get values for those indices
        val_corrs = corrs.take(idx_corrs)
        # Return highest correlated first
        corrs = zip(val_corrs, idx_corrs)
        corrs.sort(reverse=True)
        rep_cor = {reporters[i[1]]: i[0] for i in corrs}
        #query mygene to get symbol from reporter
        mg = mygene.MyGeneInfo()
        res = mg.querymany(rep_cor.keys(), scopes='reporter', fields='symbol')
        result = []
        for i in res:
            if 'notfound' in i:
                gene_id, symbol = '', ''
            else:
                gene_id, symbol = i['_id'], i['symbol']
            result.append({'id': gene_id, 'reporter': i['query'], \
                'symbol': symbol, 'value': round(rep_cor[i['query']], 4)})
        ret_type = request.GET.get('type', None)
        if ret_type is None:
            #print reporters
            from .util import ComplexEncoder
            return HttpResponse(json.dumps(result, cls=ComplexEncoder),\
                             content_type="application/json")
        else:
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename=%s.csv' \
                % ds.geo_gse_id
            writer = csv.writer(response)
            writer.writerow(result[0].keys())
            i = 0
            while(i < len(result)):
                writer.writerow(result[i].values())
                i = i + 1
            return response

    return general_json_response(GENERAL_ERRORS.ERROR_BAD_ARGS, \
                "Reporter %s not in dataset: %s." % (reporter_id, ds_id))

#just for test 503 error page redirect
def dataset_503_test(request):
    return general_json_response(GENERAL_ERRORS.ERROR_NO_PERMISSION, \
                "To enable persistent request, add \"X-Email\" HTTP header with your email address")