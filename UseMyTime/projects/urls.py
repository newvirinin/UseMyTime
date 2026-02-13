from django.urls import path
from . import views


urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('update/<int:pk>', views.ProjectUpdateView.as_view(), name='project_update'),
    path('delete/<int:pk>', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('detail/<int:pk>', views.ProjectDetailView.as_view(), name='project_detail'),
    path('archive/', views.ArchiveProjectListView.as_view(), name='projects_archive'),
    path('archivate/<int:id>', views.project_archive, name='projects_archivate'),
    path('activate/', views.project_activate, name='projects_activate'),
    path('start/', views.project_start, name='projects_start'),
    path('stop/', views.project_stop, name='projects_stop'),
    path('task/<int:id>', views.change_task_status, name='change_task_status'),
    path('timer/start/', views.project_timer_start, name='project_timer_start'),
    path('timer/stop_all/', views.stop_all_timers_on_close, name='stop_all_timers_on_close'),
    # Project review workflow
    path('projects/review/', views.ProjectReviewQueueView.as_view(), name='project_review_queue'),
    path('project/<int:pk>/submit_review/', views.project_submit_review, name='project_submit_review'),
    path('project/<int:pk>/attachment/<int:attachment_id>/', views.project_attachment_download, name='project_attachment_download'),
    path('project/<int:pk>/review/approve/', views.project_review_approve, name='project_review_approve'),
    path('project/<int:pk>/review/reject/', views.project_review_reject, name='project_review_reject'),
    path('projects/review/count/', views.project_review_count, name='project_review_count'),
]
