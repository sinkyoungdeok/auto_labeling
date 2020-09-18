from django.db import models

class Project(models.Model):
    project_name = models.CharField(max_length=30)
    project_class = models.CharField(max_length=100)
    project_create_date = models.DateTimeField(auto_now_add=True)

class Images(models.Model):
    project_id = models.IntegerField()
    data_name = models.CharField(max_length=200)
    data_class = models.CharField(max_length=200, default="None")
    data_create_date = models.DateTimeField(auto_now_add=True)
