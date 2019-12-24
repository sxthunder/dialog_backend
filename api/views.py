'''
@Author: your name
@Date: 2019-12-23 20:31:18
@LastEditTime : 2019-12-23 20:54:44
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /dialog_backend/api/views.py
'''
from django.shortcuts import render
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Create your views here.
class Reply(APIView):
    #对问题进行回复
    def post(self,request,format=None):
        print(self.request.data)
        content = {"type":"multiple_option","content":"\u8bf7\u95ee\u60a8\u6709\u4ee5\u4e0b\u75c7\u72b6\u5417\uff1f","option":[],"allow_empty":'true'}
        return Response(content,status=status.HTTP_200_OK)
