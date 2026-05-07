from django.urls import path
from api import views

urlpatterns = [
    path('health/', views.HealthView.as_view(), name='health'),
    path('forecast/', views.ResistanceForecastView.as_view(), name='forecast'),
    path('predict/', views.ResistancePredictionView.as_view(), name='predict'),
    path('timeline/', views.MutationTimelineView.as_view(), name='timeline'),
    path('antibiotics/', views.AntibioticListView.as_view(), name='antibiotics'),
    path('train/', views.TrainModelView.as_view(), name='train'),
    path('reload/', views.ReloadModelsView.as_view(), name='reload'),
]
