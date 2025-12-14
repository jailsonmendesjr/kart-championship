from django.urls import path
from . import views

urlpatterns = [
    path('', views.season_list, name='season_list'),
    path('season/<int:season_id>/', views.season_detail, name='season_detail'),
    # Nova rota abaixo:
    path('season/<int:season_id>/round/<int:round_id>/', views.round_detail, name='round_detail'),
    path('season/<int:season_id>/performance/', views.performance_analysis, name='performance_analysis'),
]