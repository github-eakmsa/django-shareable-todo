
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django.db.models import Q
from django.core.paginator import Paginator


from app_todo.forms import TodoForm
from .models import Todo

# cls.objects.filter(models.Q(a="a", b='None') | models.Q(a='None' AND b="b"))

# Create your views here.

def index(request):
    template = loader.get_template('index.html')
    return HttpResponse(template.render())

def register_page(request):
    # Check if the HTTP request method is POST (form submission)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')
         
        # Check if a user with the provided username already exists
        user = User.objects.filter(username=username)
         
        if user.exists():
            # Display an information message if the username is taken
            messages.info(request, "Username already taken!")
            return redirect('register')
         
        # Create a new User object with the provided information
        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username
        )
         
        # Set the user's password and save the user object
        user.set_password(password)
        user.save()
         
        # Display an information message indicating successful account creation
        messages.info(request, "Account created Successfully!")
        return redirect('register')
     
    # Render the registration page template (GET request)
    return render(request, 'register.html')

def login_page(request):
    # Check if the HTTP request method is POST (form submission)
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
         
        # Check if a user with the provided username exists
        if not User.objects.filter(username=username).exists():
            # Display an error message if the username does not exist
            messages.error(request, 'Invalid Username')
            return redirect('login')
         
        # Authenticate the user with the provided username and password
        user = authenticate(username=username, password=password)
         
        if user is None:
            # Display an error message if authentication fails (invalid password)
            messages.error(request, "Invalid Password")
            return redirect('login')
        else:
            # Log in the user and redirect to the home page upon successful login
            login(request, user)
            return redirect('home')
     
    # Render the login page template (GET request)
    return render(request, 'login.html')

@login_required(login_url="/login/")
def home(request):
    return render(request, "home.html")

@login_required(login_url="/login/")
def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return redirect('login')

@login_required(login_url="/login/")
def users(request):
    # dictionary for initial data with 
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    context["dataset"] = User.objects.all()

    return render(request, "user/user-list.html", context)

@login_required(login_url="/login/")
def todo_create(request):
    # dictionary for initial data with 
    # field names as keys
    context = {} 
    # add the dictionary during initialization
    if request.method == 'POST':
        form = TodoForm(request.POST or None)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.save()
            context['message']= "Successfully saved, " + request.POST.get('title')
        else:
            context['form']= form
    return render(request, "todo/todo-create.html", context)

@login_required(login_url="/login/")
def todo_update(request, pk):
    context = {}
    todo = get_object_or_404(Todo, pk=pk)
    if request.method == 'POST':
        form = TodoForm(request.POST, instance=todo)
        if form.is_valid():
            form.save()
            context['message']= "Successfully saved, " + request.POST.get('title')
    else:
        context['form'] = TodoForm(instance=todo)
    return render(request, 'todo/todo-create.html', context)

@login_required(login_url="/login/")
def todo_share(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_to_share = get_object_or_404(User, pk=user_id)
        todo.shared_with.add(user_to_share)
        return redirect('todos.mine')
    users = User.objects.exclude(pk=request.user.pk)
    return render(request, 'todo/todo-share.html', {'todo': todo, 'users': users})

@login_required(login_url="/login/")
def todos_recent(request):
    # dictionary for initial data with 
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    item_list = Todo.objects.order_by("-updated_at").filter(Q(user=request.user) | Q(shared_with=request.user))

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "todo/todos-recent.html", {"page_obj": page_obj})

@login_required(login_url="/login/")
def todos_mine(request):
    # dictionary for initial data with 
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    context["dataset"] = Todo.objects.filter(user=request.user) & Todo.objects.filter(shared_with__isnull=True)

    return render(request, "todo/todos-mine.html", context)

@login_required(login_url="/login/")
def todos_shared_in(request):
    # dictionary for initial data with 
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    context["dataset"] = Todo.objects.filter(shared_with=request.user)

    return render(request, "todo/todos-shared-in.html", context)

@login_required(login_url="/login/")
def todos_shared_out(request):
    # dictionary for initial data with 
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    context["dataset"] = Todo.objects.filter(~Q(shared_with=request.user)) & Todo.objects.filter(shared_with__isnull=False)

    return render(request, "todo/todos-shared-out.html", context)

@login_required(login_url="/login/")
def todo_detail(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    return render(request, 'todo/todo-detail.html', {'todo': todo})

@login_required(login_url="/login/")
def todo_delete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if request.method == 'POST':
        todo.delete()
        return redirect('todos.mine')
    return render(request, 'todo/todo-confirm-delete.html', {'todo': todo})

# ----------
@login_required
def get_count_shared_in_todos(request):
    shared_in = Todo.objects.filter(shared_with=request.user)
    shared_out = Todo.objects.filter(~Q(shared_with=request.user)) & Todo.objects.filter(shared_with__isnull=False)
    pending = Todo.objects.filter(shared_with=request.user)
    return JsonResponse({'shared_in': shared_in.count(), 'shared_out': shared_out.count(), 'pending': pending.count()})