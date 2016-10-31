from django.conf.urls import url
from otree.default_urls import urlpatterns

from . import views

urlpatterns.append(url(r'^example_decisions/export/$', views.export_view_json))

