from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
    url(r'^info/$', views.dataset_info, name='dataset info'),
    url(r'^data/$', views.dataset_data, name='dataset data'),
    url(r'^chart/$', views.dataset_chart, name='dataset chart'),
    url(r'^cvs/$', views.get_cvs, name='get cvs'),
)

