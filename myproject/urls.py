from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from myapp import views
from myapp.views import upload_csv, predict_fraud_single, dashboard, predict_fraud_multiple

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(url='/myapp/')),  
    path('myapp/', include('myapp.urls')),  
    path('myapp/transactions/', views.transaction_detail, name='transaction_detail'),  
    path('myapp/upload-csv/', views.upload_csv, name='upload_csv'),
    path('myapp/single_file/', views.predict_fraud_single, name='single_file'),
    path('myapp/multiple_file/', views.predict_fraud_multiple, name='multiple_file'),
    path('myapp/Dashboard/', views.dashboard, name='dashboard'),
]
