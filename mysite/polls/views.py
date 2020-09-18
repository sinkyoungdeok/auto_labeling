import os
import json
import zipfile
import csv

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from polls.models import Project, Images
from django.views.decorators.csrf import csrf_exempt
from .forms import UploadFileForm
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def project_list(request):
    project_list = Project.objects.all()
    progress_list, index_list = [], []

    index, percent = 0, 1

    for project in project_list:
        images = Images.objects.filter(project_id=project.pk)

        index += 1
        total_cnt, label_cnt = 1, 1

        for image in images:
            total_cnt += 1

            if image.data_class != "None":
                label_cnt += 1

        percent = int((label_cnt / total_cnt)*100)

        index_list.append(index)
        progress_list.append(percent)

    mylist = zip(project_list, progress_list, index_list)
    return render(request, 'blog/project_list.html', {'mylist': mylist})

def def_project_list(request):
    project_list = Project.objects.all()
    progress_list, index_list = [], []

    index, percent = 0, 1

    for project in project_list:
        images = Images.objects.filter(project_id=project.pk)

        index += 1
        total_cnt, label_cnt = 1, 1

        for image in images:
            total_cnt += 1

            if image.data_class != "None":
                label_cnt += 1

        percent = int((label_cnt / total_cnt)*100)

        index_list.append(index)
        progress_list.append(percent)

    mylist = zip(project_list, progress_list, index_list)
    return mylist


@csrf_exempt
def main_page(request):
    temp_list = []

    project_id = request.GET["project_id"]
    project_object = Project.objects.get(pk=project_id)
    project_name = project_object.project_name
    label_list = project_object.project_class[1:]
    label_list = label_list.split("&")

    images = Images.objects.filter(project_id=project_id)
    page = request.GET.get('page', 1)

    paginator = Paginator(images, 20)

    try:
        image_list = paginator.page(page)
    except PageNotAnInteger:
        image_list = paginator.page(1)
    except EmptyPage:
        image_list = paginator.page(paginator.num_pages)

    page_numbers_range = 10

    max_index = len(paginator.page_range)
    current_page = int(page) if page else 1
    start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
    end_index = start_index + page_numbers_range

    if end_index >= max_index:
        end_index = max_index

    paginator_range = paginator.page_range[start_index:end_index]
    division = int(page) // page_numbers_range
    remain = int(page) % page_numbers_range

    if remain == 0:
        division -= 1

    prev = page_numbers_range * division
    if prev == 0:
        prev = 1

    next = (page_numbers_range * (division + 1)) + 1

    if request.method == 'POST':
        id_list = request.POST.get('id_list','default')
        id_list = id_list[1:].split("&")

        temp_label_list = request.POST.get('label_list','default')
        temp_label_list = temp_label_list[1:].split("&")

        for i in range(0, len(id_list)):
            data = Images.objects.get(pk=int(id_list[i]))
            data.data_class = temp_label_list[i]
            data.save()

    context = {
        'last_page': paginator.num_pages,
        'prev_page': prev,
        'next_page': next,
        'paginator_range': paginator_range,
        'data_list':image_list,
        "label_list":label_list,
        "folder_name":project_name,
        'project_id':project_id
    }

    return render(request, 'blog/main_page.html', context)


def handle_uploaded_file(f, project_id, project_name):
    with open(os.path.join(os.getcwd(), "media/"+project_name+"/", f.name), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

            image_model = Images(project_id=project_id, data_name=f.name)
            image_model.save()


@csrf_exempt
def new_project(request):
    form = UploadFileForm()
    if request.method == 'POST':
        project_name = request.POST.get('project_name','default')
        class_string = request.POST.get('class_string','default')

        data = Project(project_name=project_name, project_class=class_string)
        data.save()

        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            os.mkdir('./media/'+project_name)
            for count, x in enumerate(request.FILES.getlist("files")):
                handle_uploaded_file(x, data.id, project_name)
            context = {'form':form,}
        
        mylist = def_project_list(request)
        return render(request, 'blog/project_list.html', {'mylist': mylist})

    else:
        form = UploadFileForm()

    return render(request, 'blog/new_project.html', {'form': form})


def csv_download(request):
    project_id = request.GET["project_id"]
    images = Images.objects.filter(project_id=project_id)

    file_path = "./media/"+project_id+".csv"

    with open(file_path, "w", newline='') as csvfile:
        fieldnames = ['name', 'label']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for image in images:
            writer.writerow({'name': image.data_name, 'label': image.data_class})


    with open(file_path, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
        return response
