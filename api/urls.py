'''
@Author: your name
@Date: 2019-12-23 20:30:03
@LastEditTime : 2019-12-30 20:05:50
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /dialog_backend/api/urls.py
'''
from django.conf.urls import include
from django.urls import path
from api import views

app_name = 'api'

urlpatterns = [
    path('reply',views.reply)
]
