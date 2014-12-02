# -*-coding: utf-8 -*-
import csv
from django.conf import settings
from django.views.decorators.http import require_http_methods
from dataset import models
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import requests
import math
from dataset.util import general_json_response, GENERAL_ERRORS
import StringIO
import mygene
from django.core.exceptions import ObjectDoesNotExist


def adopt_dataset(ds_id):
    if ds_id in settings.DEFAULT_DS_ACCESSION:
        try:
            return models.BiogpsDataset.objects.using('default_ds')\
                .get(geo_gse_id=ds_id)
        except ObjectDoesNotExist:
            return None

    try:
        return models.BiogpsDataset.objects.get(geo_gse_id=ds_id)
    except ObjectDoesNotExist:
        return None


def get_ds_factors_keys(ds, factor_by=None, group_up=False):
    """
        return an array of keys that stand for samples in ds
    """
    factors = []
    i = 1
    if factor_by is not None:
        fvs = []
    for f in ds.metadata['factors']:
        name = order_idx = color_idx = None

        # get order and color(grouping) by some certain facet
        content = f[f.keys()[0]]
        # by specified factor value 'factor_by'
        if factor_by is not None:
            v = content['factorvalue'][factor_by]
            name = v
            if v not in fvs:
                fvs.append(v)
            color_idx = fvs.index(v)
            if group_up:
                order_idx = fvs.index(v)
            else:
                order_idx = i
                i = i + 1
        # by 'order_idx' and 'color_idx' (default dataset)
        elif 'order_idx' in content and 'color_idx' in content:
                order_idx = content['order_idx']
                color_idx = content['color_idx']
        # finally by index number
        else:
            color_idx = order_idx = i
            i = i + 1

        # get sample name
        if name is None:
            if 'comment' in f[f.keys()[0]]:
                comment = f[f.keys()[0]]['comment']
                name = comment.get('Sample_title', None)
                if name is None:
                    name = comment.get('Sample_title', None)
                    if name is None:
                        name = f.keys()[0]
            else:
                name = f.keys()[0]
        factors.append({'name': name, 'order_idx': order_idx,
                        'color_idx': color_idx})
    return factors


def _contruct_meta(ds):
    preset = {'default': True, 'permission_style': 'public',
              'role_permission': ['biogpsusers'], 'rating_data':
              {'total': 5, 'avg_stars': 10, 'avg': 5}, 'display_params':
              {'color': ['color_idx'], 'sort': ['order_idx'],
               'aggregate': ['title']}}
    if type(ds.metadata['geo_gpl_id']) is dict:
        geo_gpl_id = ds.metadata['geo_gpl_id']['accession']
    else:
        geo_gpl_id = ds.metadata['geo_gpl_id']
    ret = {'id': ds.id, 'name_wrapped': ds.name, 'name': ds.name,
           'owner': ds.ownerprofile_id, 'lastmodified':
           ds.lastmodified.strftime('%Y-%m-%d %H:%M:%S'),
           'pubmed_id': ds.metadata['pubmed_id'], 'summary': ds.summary,
           'geo_gse_id': ds.geo_gse_id, 'created':
           ds.created.strftime('%Y-%m-%d %H:%M:%S'),
           'geo_gpl_id': geo_gpl_id, 'species': [ds.species]
           }
    ret.update(preset)
    return ret

@require_http_methods(["GET"])
def dataset_info(request, ds_id):
    """
        get information about a dataset
    """
    ds = adopt_dataset(ds_id)
    if ds is None:
        return HttpResponse('{"code":4004, \
                            "detail":"dataset with this id not found"}',
                            content_type="application/json")
    ret = _contruct_meta(ds)
    factors = []
    fb = request.GET.get('facet', None)
    group = request.GET.get('group', False)
    fa = get_ds_factors_keys(ds, fb, group)
    for f in fa:
        factors.append({f['name']: {"color_idx": f.get('color_idx', 0),
                        "order_idx": f.get('order_idx', 0), "title": f['name']}
                        })
    ret.update({'factors': factors})
    return general_json_response(detail=ret)


def _get_reporter_from_gene(gene):
    mg = mygene.MyGeneInfo()
    # res = mg.querymany([gene], scopes='_id', fields='reporter')
    data_json = mg.getgene(gene, fields='reporter')
    if 'reporter' not in data_json:
        return None
    reporters = []
    for i in data_json['reporter'].values():
        if type(i) is not list:
            i = [i]
        reporters = reporters + i
    return reporters


def get_dataset_data(ds, gene_id=None, reporter_id=None):
    """
        get data for dataset
    """
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


def _avg_with_deviation(li):
    average = round(float(sum(li)) / len(li), 2)
    t = 0
    for e in li:
        total = t + (e - average) ** 2
    dev = round(math.sqrt(float(total) / len(li)), 3)
    return (average, dev)


def prepare_chart_data(val_list, factors):
    for idx, e in enumerate(factors):
        e['value'] = val_list[idx]
    factors.sort(key=lambda e: e['order_idx'], reverse=True)
    res = [factors[0]]
    for e in factors[1:]:
        # a new ordered element
        if e['order_idx'] != res[-1]['order_idx']:
            # last element is 'list-value' element
            if type(res[-1]['value']) is list:
                ad = _avg_with_deviation(res[-1]['value'])
                res[-1]['dev'] = ad[1]
                res[-1]['value'] = ad[0]
            else:
                res[-1]['dev'] = 0
            # remove '.xxx' surfix in element name
            e['name'] = e["name"].split('.')[0]
            res.append(e)
        # same ordered element, put value to last element together
        else:
            # already have same ordered element
            last_value = res[-1]['value']
            if type(last_value) is list:
                last_value.append(e['value'])
            else:
                res[-1]['value'] = [last_value, e['value']]
    # last element in res
    if type(res[-1]['value']) is list:
        ad = _avg_with_deviation(res[-1]['value'])
        res[-1]['dev'] = ad[1]
        res[-1]['value'] = ad[0]
    else:
        res[-1]['dev'] = 0
    return res


def find_round(v):
    r = math.pow(10, round(math.log(v, 10))*-1+3)
    return 10 if r < 10 else r


def draw_median(ax, pos, length, label):
    ax.plot([pos, pos], [0, length], '#960096', linewidth=0.5)
    ax.text(pos, length, label, ha='center', va='bottom',
            fontsize=7, color='#960096')


def dataset_chart(request, ds_id, reporter_id):
    """
        return a static bar chart for this ds on this reporter
    """
    ds = adopt_dataset(ds_id)
    if ds is None:
        return HttpResponse('{"code":4004, "detail":"dataset with this id not \
            found"}', content_type="application/json")
    data_list = get_dataset_data(
        ds, reporter_id=reporter_id)['data'][0][reporter_id]['values']
    val_list = [float(item) for item in data_list]

    facet = request.GET.get('facet', None)
    group = request.GET.get('group', 'off')
    group = True if group == 'on' else False
    factors = get_ds_factors_keys(ds, facet, group)
    back = prepare_chart_data(val_list, factors)

    # start render part
    import numpy as np
    color_total = len(settings.BAR_COLORS)
    vals, devs, colors = [], [], []
    for idx, e in enumerate(back):
        vals.append(e['value'])
        devs.append(e['dev'])
        colors.append(settings.BAR_COLORS[e['color_idx'] % color_total])
    y_pos = np.arange(len(back))
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots()
    fig.set_size_inches(12, len(back) * 0.14)
    # draw bars
    # bar width
    width = 0.8
    # only positive error bar
    d_n = []
    d_p = []
    for idx, e in enumerate(vals):
        if e > 0:
            d_n.append(0)
            d_p.append(devs[idx])
        else:
            d_p.append(0)
            d_n.append(devs[idx])
    ax.barh(y_pos, vals, width, color=colors, edgecolor='none',
            xerr=[d_n, d_p], ecolor='#CCCCCC')
    # eliminate top padding
    plt.axis('tight')
    # x axis range, have some padding space
    li = [max(vals)*1.1, 0, min(vals)]
    plt.xlim([min(li)*1.1, max(li)*1.1])

    # x=0, draw y axis
    ax.plot([0, 0], [0, len(back)], 'k', linewidth=0.5)
    # draw median line and label
    # M
    median = np.median(vals)
    rd = find_round(max(vals))
    draw_median(ax, round(median*rd)/rd, len(back),
                'M(%s)' % str(round(median*rd)/rd))
    li = [max(vals), min(vals)]
    # try Mx3
    if median*3 < max(li) and median*3 > min(li):
        draw_median(ax, round(median*3*rd)/rd, len(back), '3xM')
    # try Mx10
    if median*10 < max(li) and median*10 > min(li):
        draw_median(ax, round(median*10*rd)/rd, len(back), '10xM')
    # set ticks attributes
    plt.tick_params(axis='x', which='both', bottom='off', top='off',
                    labelsize=8)
    plt.tick_params(axis='y', which='both', left='on', right='off',
                    direction='out')
    # draw y ticks and label
    ax.set_yticks(y_pos + width / 2)
    ax.set_yticklabels([e['name'] for e in back], fontsize=8)
    # grid on x axis
    plt.gca().xaxis.grid(linestyle='-', color='#aaaaaa')

    response = HttpResponse(content_type='image/png')
    fig.savefig(response, format='png', facecolor='w',
                bbox_inches='tight', pad_inches=0.2)
    return response


def _es_search(rpt, q=None, dft=0, start=0, size=8):
    """
        filter by "default" field and "platform" and query by keywords
        if specified
    """
    body = {"from": start, "size": size}
    # setup filter, filter is faster that query
    body['query'] = {"filtered": {"filter": {"bool": {
        "must": [{"term": {"default": dft}},
                 {"has_parent": {"parent_type": "platform", "query":
                                 {"match": {"reporters": rpt}}}}]}}
    }}
    # set query if query word is not None
    if q is not None:
        body["query"]["filtered"]["query"] = {
            "multi_match": {"query": q, "fields": ["summary", "name"]}}

    data = json.dumps(body)
    r = requests.post(settings.ES_URLS['SCH'], data=data)
    return r.json()


@csrf_exempt
def dataset_search(request):
    """
        接受查询的字段组合query和获取的第几页page
    """
    query = request.GET.get("query", None)
    gene = request.GET.get("gene", None)
    page = request.GET.get("page", 1)
    page_by = request.GET.get("page_by", 8)

    if gene is None:
        gene = settings.DEFAULT_GENE_ID
    reporters = _get_reporter_from_gene(gene)
    if reporters is None:
        return general_json_response(
            code=GENERAL_ERRORS.ERROR_NOT_FOUND, detail='no matched\
             data for gene %s.' % gene)
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
    for ds in ds_query:
        # temp_dic = {"id": ds.id, "name": ds.name, 'geo_gse_id':
        #             ds.geo_gse_id}
        # factors = get_ds_factors_keys(ds)
        # temp_dic["factors"] = [obj['name'] for obj in factors]
        temp_dic = {"id": ds.id, "name": ds.name, 'geo_gse_id':
                    ds.geo_gse_id, "sample_count": len(ds.metadata['factors'])}
        res.append(temp_dic)

    res = {"current_page": page, "total_page": total_page, "count": count,
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
        return general_json_response(
            code=GENERAL_ERRORS.ERROR_NOT_FOUND, detail='no\
            matched data for gene %s.' % gene)
    # retrive all results
    search_res = _es_search(' '.join(reporters), query, 1, 0, 9999)
    ids = [item["_source"]["geo_gse_id"]
           for item in search_res["hits"]["hits"]]
    qs = models.BiogpsDataset.objects.using('default_ds')\
        .filter(geo_gse_id__in=ids)
    res = []
    for ds in qs:
        temp_dic = {"id": ds.id, "name": ds.name, 'geo_gse_id':
                    ds.geo_gse_id, "sample_count": len(ds.metadata['factors'])}
#         factors = get_ds_factors_keys(ds)
#         temp_dic["factors"] = [obj['name'] for obj in factors]
        res.append(temp_dic)
    res = {"count": qs.count(),   "results": res}
    return general_json_response(detail=res)


@csrf_exempt
def dataset_search_all(request):
    query = request.GET.get("query", None)
    gene = request.GET.get("gene", None)
    if gene is None:
        gene = settings.DEFAULT_GENE_ID
    reporters = _get_reporter_from_gene(gene)
    if reporters is None:
        return general_json_response(
            code=GENERAL_ERRORS.ERROR_NOT_FOUND, detail='no\
            matched data for gene %s.' % gene)
    # retrive all default results(9999)
    rep = ' '.join(reporters)
    search_res = _es_search(rep, query, 1, 0, 9999)
    ids = [item["_source"]["geo_gse_id"]
           for item in search_res["hits"]["hits"]]
    qs = models.BiogpsDataset.objects.using('default_ds')\
        .filter(geo_gse_id__in=ids)
    res_default = []
    for ds in qs:
        temp_dic = {"id": ds.id, "name": ds.name, 'geo_gse_id':
                    ds.geo_gse_id, "sample_count": len(ds.metadata['factors'])}
        # factors = get_ds_factors_keys(ds)
        # temp_dic["factors"] = [obj['name'] for obj in factors]
        res_default.append(temp_dic)
    res_default = {"count": qs.count(),   "results": res_default}

    # retrive fist page non-default ds
    page_by = request.GET.get("page_by", 8)
    page_by = int(page_by)
    search_res = _es_search(rep, query, 0, 0, page_by)
    count = search_res["hits"]["total"]
    total_page = int(math.ceil(float(count) / float(page_by)))
    res = []
    ids = []
    for item in search_res["hits"]["hits"]:
        ids.append(item["_source"]["geo_gse_id"])
    ds_query = models.BiogpsDataset.objects.filter(geo_gse_id__in=ids)
    for ds in ds_query:
        temp_dic = {"id": ds.id, "name": ds.name, 'geo_gse_id':
                    ds.geo_gse_id, "sample_count": len(ds.metadata['factors'])}
        res.append(temp_dic)

    res = {"current_page": 1, "total_page": total_page, "count": count,
           "results": res}
    return general_json_response(detail={'default': res_default,
                                         'non-default': res})


def dataset_csv(request, ds_id, gene_id):
    """
         csv format file download
    """
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


@require_http_methods(["GET"])
def dataset_data(request, ds_id, gene_id):
    """
        get information about a dataset
    """
    ds = adopt_dataset(ds_id)
    if ds is None:
        return HttpResponse('{"code":4004, "detail":"dataset with this id not \
            found"}', content_type="application/json")
    ret = get_dataset_data(ds, gene_id=gene_id)
    ret['probeset_list'] = ret['data']
    del ret['data']
    return HttpResponse('{"code":0, "detail":%s}' % json.dumps(ret),
                        content_type="application/json")


@require_http_methods(["GET"])
def dataset_full_data(request, ds_id, gene_id):
    ds = adopt_dataset(ds_id)
    if ds is None:
        return general_json_response(
            GENERAL_ERRORS.ERROR_BAD_ARGS,
            "Dataset with this id does not exist.")
    data_lists = get_dataset_data(ds, gene_id=gene_id)['data']
    facet = request.GET.get('facet', None)
    group = request.GET.get('group', 'off')
    group = True if group == 'on' else False
    factors = get_ds_factors_keys(ds, facet, group)
    res = {}
    for e in data_lists:
        r = e.keys()[0]
        vals = [float(item) for item in e[r]['values']]
        res[r] = prepare_chart_data(vals, factors)
    ret = _contruct_meta(ds)
    ret.update({'faceted_values': res})
    return general_json_response(detail=ret)


def dataset_default(request):
    gene_id = request.GET.get('gene', None)
    if gene_id is None:
        gene_id = settings.DEFAULT_GENE_ID
    mg = mygene.MyGeneInfo()
    res = mg.querymany([gene_id], scopes='_id', fields='taxid')
    data_json = res[0]
    if 'taxid' not in data_json:
        return general_json_response(
            GENERAL_ERRORS.ERROR_BAD_ARGS, "Gene id: %s \
            may be invalid." % gene_id)
    species = data_json['taxid']
    try:
        ds_id = settings.DEFAULT_DATASET_MAPPING[species]
    except IndexError:
        return general_json_response(
            GENERAL_ERRORS.ERROR_BAD_ARGS, "Cannot get default\
            dataset with gene id: %s." % gene_id)
    return general_json_response(detail={'gene': int(gene_id),
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
        return general_json_response(
            GENERAL_ERRORS.ERROR_NOT_FOUND, "Cannot\
             get matrix of dataset: %s." % ds_id)
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
        # query mygene to get symbol from reporter
        mg = mygene.MyGeneInfo()
        res = mg.querymany(rep_cor.keys(), scopes='reporter', fields='symbol')
        result = []
        for i in res:
            if 'notfound' in i:
                gene_id, symbol = '', ''
            else:
                gene_id, symbol = i['_id'], i['symbol']
            result.append({'id': gene_id, 'reporter': i['query'],
                           'symbol': symbol, 'value':
                           round(rep_cor[i['query']], 4)})
        ret_type = request.GET.get('type', None)
        if ret_type is None:
            # print reporters
            from .util import ComplexEncoder
            return HttpResponse(json.dumps(result, cls=ComplexEncoder),
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

    return general_json_response(
        GENERAL_ERRORS.ERROR_BAD_ARGS, "Reporter %s not\
        in dataset: %s." % (reporter_id, ds_id))


def dataset_factors(request, ds_id):
    ds = adopt_dataset(ds_id)
    if ds is None:
        return HttpResponse(
            '{"code":4004, \
            "detail":"dataset with this id not found"}',
            content_type="application/json")
    smps = ds.metadata['factors']
    # no factor value
    if 'factorvalue' not in smps[0].values()[0]:
        return general_json_response(code=GENERAL_ERRORS.ERROR_NOT_FOUND)

    factor_keys = {}
    for smp in smps:
        fv = smp.values()[0]['factorvalue']
        for f in fv:
            if f in factor_keys.keys():
                factor_keys[f].add(fv[f])
            else:
                factor_keys[f] = set([fv[f]])
    for e in factor_keys:
        factor_keys[e] = list(factor_keys[e])
    if len(factor_keys) == 0:
        return general_json_response(code=GENERAL_ERRORS.ERROR_NOT_FOUND)
    return general_json_response(detail=factor_keys)


def dataset_503_test(request):
    """
        just for test 503 error page redirect
    """
    return general_json_response(
        GENERAL_ERRORS.ERROR_NO_PERMISSION,
        "To enable persistent request,\
        add \"X-Email\" HTTP header with your email address")
