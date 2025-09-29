from django.contrib import admin
from django.urls import path
from pricing import views  # import directly from your app
from django.http import JsonResponse

def home(request):
    return JsonResponse({"message": "Hotel Pricing API is running."})

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('api/filters/', views.get_filter_definitions, name='filters'),
    path('api/recommendations/', views.RecommendationListView.as_view(), name='recommendations'),
    path('api/batch_confirm/', views.BatchConfirmView.as_view(), name='batch_confirm'),
]
