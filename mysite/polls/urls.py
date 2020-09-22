from django.urls import path

from . import views

urlpatterns = [
    path('project_list', views.project_list),
    path('main_page', views.main_page),
    path('new_project', views.new_project),
    path('csv_download', views.csv_download),
    path('new_model', views.new_model),
]
