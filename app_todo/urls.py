from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),    # Home page
    path('register/', views.register_page, name='register'),  # Registration page
    path('login/', views.login_page, name='login'),    # Login page
    path('home/', views.home, name='home'),    # User dashboard page
    path('logout/', views.logout_view, name='logout'),    # Logout 
    
    path('todos/create/', views.todo_create, name='todos.create'),
    path('todos/mine/', views.todos_mine, name='todos.mine'),
    path('todos/recent/', views.todos_recent, name='todos.recent'),
    path('todos/shared-in/', views.todos_shared_in, name='todos.shared_in'),
    path('todos/shared-out/', views.todos_shared_out, name='todos.shared_out'),
    path('todos/<int:pk>/', views.todo_detail, name='todos.detail'),
    path('todos/<int:pk>/edit/', views.todo_update, name='todos.update'),
    path('todos/<int:pk>/delete/', views.todo_delete, name='todos.delete'),
    path('todos/<int:pk>/share/', views.todo_share, name='todos.share'),

    path('count/shared-in-todos/', views.get_count_shared_in_todos, name='get_count_shared_in_todos'),

    path('users/', views.users, name='users'),
    # path('users/new/', views.user_create, name='users.create'),
]