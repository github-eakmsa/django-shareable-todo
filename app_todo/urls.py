from django.urls import path, include
from django.conf.urls.i18n import i18n_patterns
from . import views
from app_todo.views import CustomPasswordChangeView, CustomPasswordChangeDoneView, NotificationViewSet, SaveFCMTokenView
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet)

urlpatterns = [
    path('', views.index, name='index'),    # Home page
    path('about/', views.about, name='about'),    # About page
    path('contact/', views.contact, name='contact'),    # Contact page
    path('register/', views.register_page, name='register'),  # Registration page
    path('verify-email/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('login/', views.login_page, name='login'),    # Login page
    path('dashboard/', views.dashboard, name='dashboard'),    # User dashboard page
    path('user/profile', views.user_profile, name='users.profile'),    # User profile page
    path('user/profile/update', views.user_profile_update, name='users.profile_update'),    # User profile update
    path('language/change', views.language_change, name='language.change'),    # Language change page
    # Language switcher
    path('i18n/', include('django.conf.urls.i18n')),
    path('logout/', views.logout_view, name='logout'),    # Logout 
    path('password-change/', CustomPasswordChangeView.as_view(), name='password_change'),
    path('password-change/done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),

    path('todos/create/', views.todo_create, name='todos.create'),
    path('todos/recent/', views.todos_recent, name='todos.recent'),    
    path('todos/pending/', views.todos_pending, name='todos.pending'),
    path('todos/mine/', views.todos_mine, name='todos.mine'),
    path('todos/all-mine/', views.todos_all_mine, name='todos.all-mine'),
    path('todos/shared-in/', views.todos_shared_in, name='todos.shared_in'),
    path('todos/shared-out/', views.todos_shared_out, name='todos.shared_out'),
    path('todos/archived/', views.todos_archived, name='todos.archived'),
    path('todos/trashed/', views.todos_trashed, name='todos.trashed'),
    path('todos/shared-with/<int:pk>', views.todos_by_user, name='todos.by_user'),
    path('todos/<int:pk>/', views.todo_detail, name='todos.detail'),
    path('todos/<int:pk>/edit/', views.todo_update, name='todos.update'),
    path('todos/<int:pk>/delete/', views.todo_delete, name='todos.delete'),
    path('todos/<int:pk>/restore/', views.todo_restore, name='todos.restore'),
    path('todos/<int:pk>/share/', views.todo_share, name='todos.share'),
    path('todos/<int:pk>/change-status/', views.todo_status_change, name='todos.status_change'),

    path('workspaces/create/', views.workspace_create, name='workspaces.create'),
    path('workspaces/list/', views.workspaces_list, name='workspaces.list'),
    path('workspaces/<int:pk>/', views.workspace_detail, name='workspaces.detail'),
    path('workspaces/<int:pk>/edit/', views.workspace_update, name='workspaces.update'),
    path('workspaces/change/', views.workspace_change, name='workspaces.change'),
    path('workspaces/<int:pk>/share/', views.workspace_share, name='workspaces.share'),
    path('search/result/', views.search_result, name='search_result'),

    path('count/shared-in-todos/', views.get_count_todos, name='get_count_todos'),
    path('users/search/', views.search_users, name='search_users'),
    path('search/', views.grand_search, name='grand_search'),

    path('notifications/unread', views.notifications_unread, name='notifications.unread'),
    path('test-email/', views.testMail, name='test-email'),
    path('', include(router.urls)),
    path('api/save-fcm-token/', SaveFCMTokenView.as_view(), name='save_fcm_token'),
    # Other URLs
    path('firebase-messaging-sw.js', TemplateView.as_view(template_name="firebase-messaging-sw.js", content_type='application/javascript')),
    path('datatable/', views.datatable, name='datatable'),
    path('data-table/', views.datatable_view, name='datatable_view'),

]
