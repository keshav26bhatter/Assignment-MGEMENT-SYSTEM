from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='home'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/assignments/create/', views.assignment_create, name='assignment_create'),
    path('teacher/assignments/<int:pk>/edit/', views.assignment_edit, name='assignment_edit'),
    path('teacher/assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),
    path('teacher/assignments/<int:pk>/submissions/', views.assignment_submissions, name='assignment_submissions'),
    path('teacher/submissions/<int:pk>/evaluate/', views.evaluate_submission, name='evaluate_submission'),

    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/assignments/<int:pk>/', views.student_assignment_detail, name='student_assignment_detail'),
]
