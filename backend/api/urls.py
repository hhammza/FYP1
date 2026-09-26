from django.urls import path
from api import views

urlpatterns = [
    path('health/', views.HealthView.as_view(), name='health'),
    path('forecast/', views.ResistanceForecastView.as_view(), name='forecast'),
    path('predict/', views.ResistancePredictionView.as_view(), name='predict'),
    path('timeline/', views.MutationTimelineView.as_view(), name='timeline'),
    path('antibiotics/', views.AntibioticListView.as_view(), name='antibiotics'),
    path('vocabulary/', views.VocabularyView.as_view(), name='vocabulary'),
    path('train/', views.TrainModelView.as_view(), name='train'),
    path('models/', views.ModelReportView.as_view(), name='models'),
    path('genes/', views.GeneReportView.as_view(), name='genes'),
    path('genes/matrix.csv', views.GeneMatrixCSVView.as_view(), name='gene-matrix-csv'),
    path('genes/info.csv', views.GeneInfoCSVView.as_view(), name='gene-info-csv'),
    path('genes/<str:genome_id>/', views.GeneLookupView.as_view(), name='gene-lookup'),
    path('reload/', views.ReloadModelsView.as_view(), name='reload'),
]
