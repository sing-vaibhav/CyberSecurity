from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('',          views.index,           name='index'),
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('resources/',  views.resources,       name='resources'),

    # REST API
    path('api/subscribe/',    views.subscribe,     name='api-subscribe'),
    path('api/quiz/',         views.submit_quiz,   name='api-quiz'),
    path('api/report/',       views.report_threat, name='api-report'),
    path('api/track/',        views.track_visit,   name='api-track'),
    path('api/stats/',        views.get_stats,     name='api-stats'),
]
