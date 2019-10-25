# coding:utf-8
from django.urls import path
import my_RTB.views

urlpatterns = [
    # path('login/',login.views.login,),
    # path('',my_RTB.views.index,),
    path('RTB',my_RTB.views.RTB,),
    path('',my_RTB.views.get_log,),
    path('size.html',my_RTB.views.get_size,),
]
