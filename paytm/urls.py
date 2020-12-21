from django.conf.urls import url
from paytm import views


app_name = 'paytm'

urlpatterns = [
    url(r'^$', views.AboutView.as_view(), name='about'),
    url(r'^pay/$', views.initiate_payment, name='pay'),
    url(r'^callback/$', views.paytm_callback, name='callback')
]