from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pets/', views.pet_list_view, name='pet_list'),
    path('pets/add/', views.pet_create_view, name='pet_create'),
    path('pets/<int:pk>/', views.pet_detail_view, name='pet_detail'),
    path('pets/<int:pk>/edit/', views.pet_update_view, name='pet_update'),
    path('pets/<int:pk>/invite/', views.pet_invite_view, name='pet_invite'),
    path('checkin/', views.checkin_select_pet_view, name='checkin_select_pet'),
    path('pets/<int:pet_id>/checkin/', views.checkin_create_view, name='checkin_create'),
    path('invites/<uuid:token>/accept/', views.invite_accept_view, name='invite_accept'),
    path('pets/<int:pk>/invites/<int:invite_pk>/delete/', views.invite_delete_view, name='invite_delete'),
]
