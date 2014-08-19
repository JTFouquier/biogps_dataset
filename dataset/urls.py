from django.conf.urls import patterns,  url
import views

urlpatterns = patterns('',
    url(r'^meta/(?P<ds_id>\d+)/$', views.dataset_info, name='dataset meta'),
    url(r'^data/(?P<ds_id>\d+)/gene/(?P<gene_id>\d+)/$', \
        views.dataset_data, name='dataset data'),
    url(r'^chart/(?P<ds_id>\d+)/reporter/(?P<reporter_id>.+)/$',\
         views.dataset_chart, name='dataset chart'),
    #url(r'^chart/$', views.dataset_chart, name='dataset chart'),
    url(r'^csv/(?P<ds_id>\d+)/gene/(?P<gene_id>.+)/$', \
        views.dataset_csv, name='dataset csv'),
    url(r'^search/$', views.dataset_search, name='dataset search')
)
