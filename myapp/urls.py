from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # path('myapp/transactions/', views.transaction_detail, name='transaction_detail'),
    #path('myapp/dashboard/', views.dashboard, name='dashboard'),
    path('', views.index, name='index'),
    path('', views.home, name='home'),
    path('predictions/', views.predictions, name='predictions'),
]