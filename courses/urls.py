from django.urls import path
from . import views

urlpatterns = [
    # Intelligent Home Redirect
    path('', views.home_redirect, name='home'),

    # Authentication Routes
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),

    # Doctor Portal
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/courses/', views.doctor_courses, name='doctor_courses'),
    path('doctor/courses/<int:course_id>/', views.doctor_course_detail, name='doctor_course_detail'),
    path('doctor/courses/<int:course_id>/lectures/add/', views.doctor_lecture_add, name='doctor_lecture_add'),
    path('doctor/courses/<int:course_id>/lectures/<int:lecture_id>/edit/', views.doctor_lecture_edit, name='doctor_lecture_edit'),
    path('doctor/courses/<int:course_id>/lectures/<int:lecture_id>/delete/', views.doctor_lecture_delete, name='doctor_lecture_delete'),
    path('doctor/enrollments/', views.doctor_enrollment_requests, name='doctor_enrollment_requests'),
    path('doctor/enrollments/<int:request_id>/approve/', views.doctor_enrollment_approve, name='doctor_enrollment_approve'),
    path('doctor/enrollments/<int:request_id>/reject/', views.doctor_enrollment_reject, name='doctor_enrollment_reject'),
    path('doctor/profile/', views.doctor_profile, name='doctor_profile'),

    # Student Portal
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/courses/', views.student_courses, name='student_courses'),
    path('student/courses/<int:course_id>/enroll/', views.student_course_enroll, name='student_course_enroll'),
    path('student/my-courses/', views.student_my_courses, name='student_my_courses'),
    path('student/courses/<int:course_id>/', views.student_course_detail, name='student_course_detail'),
    path('student/courses/<int:course_id>/lectures/<int:lecture_id>/', views.student_lecture_detail, name='student_lecture_detail'),
    path('student/profile/', views.student_profile, name='student_profile'),

    # UI Design Preview (Phase 1)
    path('preview/', views.preview_phase1, name='preview_phase1'),
]
