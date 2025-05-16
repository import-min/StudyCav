from django.urls import path, include
from django.contrib import admin
from . import views
from .views import check_and_login
from .views import upload_file, group_detail
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),

    path('', views.home, name='home'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),  # admin-only dashboard
    path('common-dashboard/', views.common_dashboard, name='common_dashboard'),  # common user dashboard
    path('login/', views.login_view, name='login'),  # custom login view
    path('dashboard/', views.dashboard, name='dashboard'),  # Role-based dashboard after login
    path('google-login/callback/', views.google_login_callback, name='google_login_callback'),  # Google callback

    path('calendar/', views.calendar_view, name='calendar_view'),
    path('create-event/', views.create_event, name='create_event'),
    #path('join-group/<int:group_id>/', views.join_group, name='join_group'),
    path('leave-group/<int:group_id>/', views.leave_group, name='leave_group'),
    path('create-group/', views.create_study_group, name='create_group'),
    path('get-events/', views.get_events, name='get_events'),
    path('about/', views.about_page, name='about_page'),

    path('check_and_login/', views.check_and_login, name='check_and_login'),
    path('post_login_redirect/', views.post_login_redirect, name='post_login_redirect'),
    path('group/<str:group_name>/upload/', upload_file, name='upload_file'),
    path('group/<str:group_name>/', views.group_detail, name='group_detail'),
    path('study-group/<int:group_id>/', views.study_group_details, name='study_group_details'),
    path('admin_study_groups/', views.admin_study_groups, name='admin_study_groups'),
    path('study_groups/', views.common_user_study_groups, name='common_user_study_groups'),
    path('delete_study_group/<int:group_id>/', views.delete_study_group, name='delete_study_group'),
    path('study-groups/', views.study_group_list, name='study_group_list'),
    path('group/<int:group_id>/edit/<int:document_id>/', views.edit_document, name='edit_document'),
    path('group/<int:group_id>/delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('group/<int:group_id>/delete_group/', views.delete_group, name='delete_group'),
    path('study-group/<int:study_group_id>/admin_view/', views.adminView_study_group_details, name='adminView_study_group_details'),
    path('group/<int:group_id>/admin_view/', views.adminView_group_detail, name='adminView_group_detail'),
    path('group/<int:group_id>/delete/<int:document_id>/admin_view/', views.adminView_delete_document, name='adminView_delete_document'),
    path('group/<int:study_group_id>/admin_view/remove_member/<int:member_id>/', views.remove_member,
         name='remove_member'),
    path('group/<int:study_group_id>/admin_view/delete_event/<int:event_id>/', views.delete_event,
        name='delete_event'),
    path('group/<int:group_id>/chatRoom/', views.chat_room_view, name='chat_room_view'),
    path('group/<int:group_id>/chatRoom/admin_view', views.adminView_chat_room_view, name='adminView_chat_room_view'),
    path('group/<int:study_group_id>/chatRoom/delete_message/<int:message_id>/', views.delete_message,
         name='delete_message'),
    path('group/<int:group_id>/delete_group/', views.delete_group, name='delete_group'),
    path('study-group/<int:group_id>/request/', views.request_to_join_group, name='request_to_join_group'),
    path('accept-join-request/<int:request_id>/', views.accept_join_request, name='accept_join_request'),
    path('reject-join-request/<int:request_id>/', views.reject_join_request, name='reject_join_request'),
    path('logout/', views.logout_view, name='logout_view'),

]



