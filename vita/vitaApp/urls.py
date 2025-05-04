
from .views import index, predict, user_register,index1,home,user_edit, transcribe, data,welcome,progress
# heart_rate_view)
from django.urls import path

urlpatterns = [
    path('', index, name='index'),
    path('welcome',welcome,name='welcome'),
    path('predict/', predict, name='predict'),
    # path('heart-rate/', heart_rate_view, name='heart_rate'),
    path('firebase/',index1,name="firebase"),
    path('homepage/<int:user_id>/',home,name="home"),
    path('form/',user_register,name='user_register'),
    path('edit/<int:user_id>/',user_edit, name='user_edit'),
    path('transcribe/', transcribe, name='transcribe'),
    path('predict/<int:user_id>', predict, name='predict'),
    path('data/', data, name='data'),
    path('progress/',progress, name='progress'),

]