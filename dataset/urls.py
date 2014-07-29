from django.conf.urls import patterns,  url
import views

urlpatterns = patterns('',
    url(r'^info/$', views.dataset_info, name='dataset info'),
    url(r'^data/$', views.dataset_data, name='dataset data'),
    url(r'^chart/$', views.dataset_chart, name='dataset chart'),
    url(r'^csv/$', views.get_csv, name='dataset csv'),
)
