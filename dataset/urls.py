from django.conf.urls import patterns,  url
from dataset import views

urlpatterns = patterns(
    '',
    url(r'^meta/(?P<ds_id>.+)/$', views.dataset_info,
        name='dataset meta'),
    url(r'^data/(?P<ds_id>.+)/gene/(?P<gene_id>.+)/$',
        views.dataset_data, name='dataset data'),
    # return meta data, value together with support for facet and grouping
    url(r'^full-data/(?P<ds_id>.+)/gene/(?P<gene_id>.+)/$',
        views.dataset_full_data, name='dataset full data'),
    url(r'^chart/(?P<ds_id>.+)/reporter/(?P<reporter_id>.+)/$',
        views.dataset_chart, name='dataset chart'),
    url(r'^csv/(?P<ds_id>.+)/gene/(?P<gene_id>.+)/$',
        views.dataset_csv, name='dataset csv'),
    url(r'^search/$', views.dataset_search, name='dataset search'),
    url(r'^search/default/$', views.dataset_search_default,
        name='dataset search default'),
    # return first page non-default and all default ds
    url(r'^search/all/$', views.dataset_search_all,
        name='dataset search all'),
    url(r'^default/$', views.dataset_default, name='dataset default'),
    url(r'^correlation/(?P<ds_id>.+)/reporter/(?P<reporter_id>.+)/min/(?P<min_corr>.+)/$',
        views.dataset_correlation,
        name='dataset correlation'),
    url(r'^factors/(?P<ds_id>.+)/$', views.dataset_factors,
        name='dataset factors'),

    # url(r'^503_test/$', views.dataset_503_test, name='dataset 503 test'),
)
