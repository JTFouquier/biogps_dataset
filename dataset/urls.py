from django.conf.urls import patterns,  url
import views

urlpatterns = patterns('',
    url(r'^info/$', views.dataset_info, name='dataset info'),
    url(r'^data/$', views.dataset_data, name='dataset data'),
    url(r'^(?P<_id>\d+)/chart/(?P<reporter>.+)/$', views.dataset_chart,\
        name='dataset chart'),
    #url(r'^chart/$', views.dataset_chart, name='dataset chart'),
    url(r'^csv/$', views.dataset_csv, name='dataset csv'),
    url(r'^search/$', views.dataset_search, name='dataset search')
)
