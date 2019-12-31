'''
@Author: your name
@Date: 2019-12-23 20:31:18
@LastEditTime : 2019-12-30 20:18:28
@LastEditors  : Please set LastEditors
@Description: In User Settings Edit
@FilePath: /dialog_backend/api/views.py
'''
from django.shortcuts import render
from django.http import HttpResponse
from api import utils
from qa import main

def reply(request):
    if request.method == 'GET':
        question = request.GET['question']
        
        #意图识别
        intention = utils.detect_intention(question)

        if intention == 'qa':
            result, lexical_seq, question_type_tuple = main.parsing(question)
            return HttpResponse(result)
        else:
            return None
            

        