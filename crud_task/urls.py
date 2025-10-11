from django.urls import path
from . import views


urlpatterns = [
    path("", views.index, name="home"),
    path("register/", views.register, name="register"),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('compte/', views.compte, name='compte'),
    path("add_user/", views.add_user, name="add_user"),
    path("add_project/", views.add_project, name="add_project"),
    path("compte/<int:project_id>/delete_project/", views.del_project, name="delete"),
    path('add_task/', views.add_task, name='add_task'),
    path("delete_task/<int:task_id>/", views.delete_task, name="delete_task"),
    # Dans votre urls.py
    path('toggle-task/<int:task_id>/', views.toggle_task_status, name='toggle_task_status'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('reactivate-task/<int:task_id>/', views.reactivate_task, name='reactivate_task'),
]
