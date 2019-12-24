'''
@Author: your name
@Date: 2019-12-23 20:30:03
@LastEditTime : 2019-12-23 20:50:27
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /dialog_backend/api/urls.py
'''
from django.conf.urls import include
from django.urls import path
from api import views

app_name = 'api'

urlpatterns = [
    path('reply',views.Reply.as_view())
]
