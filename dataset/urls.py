from django.conf.urls import patterns,  url
import views

urlpatterns = patterns('',
    url(r'^meta/(?P<ds_id>.+)/$', views.dataset_info, name='dataset meta'),
    url(r'^data/(?P<ds_id>.+)/gene/(?P<gene_id>.+)/$', \
        views.dataset_data, name='dataset data'),
    url(r'^chart/(?P<ds_id>.+)/reporter/(?P<reporter_id>.+)/$',\
         views.dataset_chart, name='dataset chart'),
    #url(r'^chart/$', views.dataset_chart, name='dataset chart'),
    url(r'^csv/(?P<ds_id>.+)/gene/(?P<gene_id>.+)/$', \
        views.dataset_csv, name='dataset csv'),
    url(r'^search/$', views.dataset_search, name='dataset search'),
    url(r'^search/default/$', views.dataset_search_default, name='dataset search default'),
    url(r'^default/$', views.dataset_default, name='dataset default'),
    url(r'^correlation/(?P<ds_id>.+)/reporter/(?P<reporter_id>.+)/min/(?P<min_corr>.+)/$', views.dataset_correlation, \
        name='dataset correlation')
)
