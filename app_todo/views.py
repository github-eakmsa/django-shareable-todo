
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from app_todo.forms import FeedbackForm, TodoForm, CommentForm, CustomPasswordChangeForm, TodoStatusChangeForm, WorkspaceForm
from app_todo.notifications.service import NotificationService
from app_todo.serializers import NotificationSerializer, FCMTokenSerializer, TodoSerializer
from .models import ActiveWorkspace, Feedback, Notification, Todo, TodoAttachment, TodoTimeline, UserProfile, Workspace
from django.conf import settings
from .utils import send_email

from django.template.defaulttags import register
from django.urls import reverse
from datetime import date, datetime
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
# ---
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
# ---
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
# ---
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from pyfcm import FCMNotification
from rest_framework.views import APIView

# ---
@register.filter(name='split')
def split(value, key):
    return value.split(key)

@register.filter(name='format_todo_status')
def format_todo_status(value, key):
    text = ''
    if key in [Todo.IN_PROGRESS, Todo.ON_PRIORITY]:
        text = '<span class="text-primary">'+ value +'</span>'
    elif key in [Todo.PENDING, Todo.ON_HOLD, Todo.NEEDS_INFO]:
        text = '<span class="text-warning">'+ value +'</span>'
    elif key in [Todo.CANCELLED]:
        text = '<span class="text-danger">'+ value +'</span>'
    elif key in [Todo.COMPLETED]:
        text = '<span class="text-success">'+ value +'</span>'
    return text

@register.filter(name='expired_due_date')
def expired_due_date(value):
    today = date.today()
    text = value
    if type(value) is date:
        if value <= today:
            text = '<span class="text-danger">'+ str(value) +'</span>'
    return text

# ---
def index(request):
    return render(request, 'index.html')

def features(request):
    return render(request, 'features.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    context = {}
    # Check if the HTTP request method is POST (form submission)
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            if request.user.is_authenticated:
                feedback.user = request.user
            feedback.save()
            context['message'] = "Feedback submitted successfully!"

    return render(request, 'contact.html', context)

def register_page(request):
    context = {}
    # Check if the HTTP request method is POST (form submission)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
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
            email=email,
            username=username,
            is_active=False
        )
         
        # Set the user's password and save the user object
        user.set_password(password)
        user.save()

        verify_email = send_verification_email(user, request)
         
        # Display an information message indicating successful account creation
        messages.info(request, "Account created Successfully. Please check your mailbox. a message has been sent to verify your email address.")
        return redirect('register')
     
    # Render the registration page template (GET request)
    return render(request, 'register.html', context)

def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('login')
    else:
        return render(request, 'errors/email_verification_failed.html')
    
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
            # Log in the user and redirect to the dashboard page upon successful login
            login(request, user)
            if ('next' in request.GET) & bool(request.GET.get('next')):
                return redirect(request.GET.get('next'))
            else:
                return redirect('dashboard')
     
    # Render the login page template (GET request)
    return render(request, 'login.html')

@login_required()
def dashboard(request):
    context = {}
    if get_active_workspace(request):
        context['workspaces'] = Workspace.objects.filter(
            Q(user=request.user) |
            Q(shared_with=request.user)
            ).count()
        context['shared_in_todos'] = Todo.objects.filter(
            Q(workspace=get_active_workspace(request)) & 
            Q(status=settings.ACTIVE) &
            ~Q(user=request.user) & 
            Q(shared_with=request.user) &
            Q(shared_with__isnull=False)
            ).count()
        context['shared_out_todos'] = Todo.objects.filter(
            Q(workspace=get_active_workspace(request)) & 
            Q(status=settings.ACTIVE) &
            Q(user=request.user) &
            Q(shared_with__isnull=False)
            ).count()
        context['pending_todos'] = Todo.objects.filter(
            Q(workspace=get_active_workspace(request)) & 
            (Q(user=request.user) | Q(shared_with=request.user)) & 
            Q(status=settings.ACTIVE) & 
            Q(todo_status=Todo.PENDING)        
            ).count()
        context['todays_todos'] = Todo.objects.filter(
            Q(workspace=get_active_workspace(request)) & 
            (Q(user=request.user) | Q(shared_with=request.user)) & 
            Q(status=settings.ACTIVE) & 
            Q(expires_at=date.today())        
            ).count()
    return render(request, "dashboard.html", context)

@login_required()
def datatable(request):
    return render(request, "datatable.html")

def datatable_view(request):
    # Get parameters from the request
    draw = int(request.GET.get('draw', 0))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search', '')
    order_column = request.GET.get('order[0][column]', 0)
    order_dir = request.GET.get('order[0][dir]', '')

    # start_roll_number = (start - 1) * length + 1

    # Filter data based on search value
    queryset = Todo.objects.filter(Q(title__icontains=search_value) | Q(body__icontains=search_value))

    # Order data
    order_column_index = int(order_column)
    # order_field = Todo._meta.get_fields()[order_column_index].name
    order_field = ('title', 'body')[order_column_index]
        
    order_by_clause = []
    if order_field:
        if order_dir == 'desc':
            order_by_clause.append(f'-{order_field}')
        else:
            order_by_clause.append(order_field)

    queryset = queryset.order_by(*order_by_clause)

    # Paginate data
    paginator = Paginator(queryset, length)
    try:
        page_obj = paginator.page(start // length + 1)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    # Serialize data
    serialized_data = TodoSerializer(page_obj, many=True, context={'roll_number_index': 0}).data

    # Iterate through serialized data and update roll_no
    for index, item in enumerate(serialized_data):
        item['roll_no'] = start + index + 1

    # Prepare response data
    response_data = {
        'draw': draw,
        'recordsTotal': queryset.count(),
        'recordsFiltered': queryset.count(),
        'data': serialized_data
    }

    return JsonResponse(response_data)

@login_required()
def user_profile(request):
    context = {}
    if 'user' in request.GET:
        usr = get_object_or_404(User, pk=request.GET.get('user'))
        context['profile'] = usr
        context['other'] = True
    else:
        context['profile'] = request.user

    context['media_url']=settings.MEDIA_URL
    context['next']=request.GET.get('next')
    return render(request, "user/user-profile.html", context)

@login_required()
def user_profile_update(request):
    context = {}
    # Check if the HTTP request method is POST (form submission)
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        currUser = get_object_or_404(User, pk=request.user.id)
        currUser.first_name=first_name
        currUser.last_name=last_name
        currUser.save()
        
        if 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            profPic = UserProfile.objects.filter(user=request.user).first()
            if not profPic:
                profPic = UserProfile()
                profPic.user = request.user
            profPic.avatar = profile_picture
            profPic.save()
        
        # Display an information message indicating successful account creation
        context['user'] = currUser
        context['message'] = "Profile updated Successfully!"
     
    return render(request, 'user/user-profile-update.html', context)

@login_required()
def language_change(request):
    context = {}
    context['LANGUAGES'] = settings.LANGUAGES
    context['next']=request.GET.get('next')
    return render(request, "user/language-change.html", context)

# @login_required()
class CustomPasswordChangeView(PasswordChangeView):
    form_class = CustomPasswordChangeForm
    template_name = 'registration/password_change_form.html'

# @login_required()
class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    # form_class = CustomPasswordChangeForm
    template_name = 'registration/password_change_done.html'

@login_required()
def logout_view(request):
    logout(request)
    # Redirect to a success page.
    return redirect('index')

# @login_required()
# def handle_uploaded_file(uploadedFile):
#     with open(settings.PATH_FOR_TODO_ATTACHMENTS, "wb+") as destination:
#         for chunk in uploadedFile.chunks():
#             destination.write(chunk)

@login_required()
def todo_create(request):
    # dictionary for initial data with 
    # field names as keys
    context = {} 
    # add the dictionary during initialization
    if request.method == 'POST':
        form = TodoForm(request.POST, request.FILES)
        if form.is_valid():
            todo = form.save(commit=False)
            todo.user = request.user
            todo.workspace = get_active_workspace(request)
            todo.save()
            if 'attachments' in request.FILES:
                attachments = request.FILES.getlist('attachments')
                for file in attachments:
                    todo_attach = TodoAttachment(todo=todo, attachment=file)
                    todo_attach.save()
            timelineLog = TodoTimeline()
            timelineLog.todo = todo
            timelineLog.user = request.user
            timelineLog.todo_status = todo.todo_status
            timelineLog.save()
            context['message']= "Successfully saved, " + request.POST.get('title')
        else:
            context['form']= form
    context['next']=request.GET.get('next')
    return render(request, "todo/todo-create.html", context)

@login_required()
def todo_update(request, pk):
    context = {}
    todo = get_object_or_404(Todo, pk=pk)
    context['form'] = TodoForm(instance=todo)
    context['record_statuses'] = settings.RECORD_STATUS_CHOICES
    if request.method == 'POST':
        form = TodoForm(request.POST, request.FILES, instance=todo)
        if form.is_valid():
            form.save()
            if 'attachments' in request.FILES:
                attachments = request.FILES.getlist('attachments')
                if len(attachments) > 0:
                    old_attachments = TodoAttachment.objects.filter(todo=todo)
                    for attached in old_attachments:
                        attached.delete()
                    for file in attachments:
                        todo_attach = TodoAttachment(todo=todo, attachment=file)
                        todo_attach.save()
            context['message']= "Successfully saved, " + request.POST.get('title')
            context['form'] = TodoForm(instance=todo)
    context['next']=request.GET.get('next')
    return render(request, 'todo/todo-create.html', context)

@login_required()
def todo_share(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    context = {}
    users = User.objects.exclude(pk=request.user.pk).exclude(pk=todo.user.pk).exclude(pk__in = todo.shared_with.only('id'))
    context['todo'] = todo
    context['users'] = users
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_to_share = get_object_or_404(User, pk=user_id)

        if user_to_share not in todo.shared_with.all():
            todo.shared_with.add(user_to_share)

        workspace = todo.workspace

        if user_to_share not in workspace.shared_with.all():
            workspace.shared_with.add(user_to_share)

        notification_service = NotificationService()
        
        notifyContext = {
            'actorFirstName': request.user.first_name,
            'todoTitle': todo.title,
            'todoShareDate': str(datetime.now()),
            'todoDetailLink': str(settings.APP_URL)+str(reverse("todos.detail", args=[todo.id])),
        }

        notification_service.send_notification(user=user_to_share, template_name="todo_share", context=notifyContext, channels=["in_app", "push"])
            
        context['message']= "Successfully shared the ToDo."
    context['next']=request.GET.get('next')
    return render(request, 'todo/todo-share.html', context)

@login_required()
def todos_recent(request):
    # dictionary for initial data with 
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    item_list = Todo.objects.order_by("-updated_at").filter(
        Q(workspace=get_active_workspace(request)) & 
        (Q(user=request.user) | Q(shared_with=request.user)) & 
        Q(status=settings.ACTIVE)
        )

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj

    return render(request, "todo/todos-recent.html", context)

@login_required()
def todos_pending(request):
    # dictionary for initial data with 
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    item_list = Todo.objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        (Q(user=request.user) | Q(shared_with=request.user)) & 
        Q(status=settings.ACTIVE) & 
        Q(todo_status=Todo.PENDING)
        )

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj

    return render(request, "todo/todos-pending.html", context)

@login_required()
def todos_mine(request):
    # dictionary for initial data with 
    # field names as keys
    context ={}
 
    # add the dictionary during initialization
    item_list = Todo.objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        Q(user=request.user) & 
        ~Q(status=settings.ARCHIVED) & 
        Q(shared_with__isnull=True)
    )
    
    if ('date_start' in request.GET) & ('date_end' in request.GET) & bool(request.GET.get('date_start')) & bool(request.GET.get('date_end')):
        dateStart = request.GET.get('date_start')
        dateEnd = request.GET.get('date_end')
        item_list = item_list.filter(expires_at__gte=dateStart, expires_at__lte=dateEnd)
    elif ('date_start' in request.GET) & bool(request.GET.get('date_start')):
        dateStart = request.GET.get('date_start')
        item_list = item_list.filter(expires_at=dateStart)
    elif ('date_end' in request.GET) & bool(request.GET.get('date_end')):
        dateEnd = request.GET.get('date_end')
        item_list = item_list.filter(expires_at=dateEnd)

    if ('todo_status' in request.GET) & bool(request.GET.get('todo_status')):
        todoStatus = request.GET.get('todo_status')
        item_list=item_list.filter(todo_status=todoStatus)

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['currStatus'] = int(request.GET.get('todo_status')) if request.GET.get('todo_status') else ''
    context['form'] = request.GET
    context['page_obj'] = page_obj
    context['todo_status'] = settings.TODO_STATUS_CHOICES

    return render(request, "todo/todos-mine.html", context)

@login_required()
def todos_all_mine(request):
    # dictionary for initial data with 
    # field names as keys
    context = {}
 
    # add the dictionary during initialization
    item_list = Todo.objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        (Q(user=request.user) | Q(shared_with=request.user)) &
        ~Q(status=settings.ARCHIVED)
        )
    
    if ('date_start' in request.GET) & ('date_end' in request.GET) & bool(request.GET.get('date_start')) & bool(request.GET.get('date_end')):
        dateStart = request.GET.get('date_start')
        dateEnd = request.GET.get('date_end')
        item_list = item_list.filter(expires_at__gte=dateStart, expires_at__lte=dateEnd)
    elif ('date_start' in request.GET) & bool(request.GET.get('date_start')):
        dateStart = request.GET.get('date_start')
        item_list = item_list.filter(expires_at=dateStart)
    elif ('date_end' in request.GET) & bool(request.GET.get('date_end')):
        dateEnd = request.GET.get('date_end')
        item_list = item_list.filter(expires_at=dateEnd)

    if ('todo_status' in request.GET) & bool(request.GET.get('todo_status')):
        todoStatus = request.GET.get('todo_status')
        item_list=item_list.filter(todo_status=todoStatus)

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['currStatus'] = int(request.GET.get('todo_status')) if request.GET.get('todo_status') else ''
    context['form'] = request.GET
    context['page_obj'] = page_obj
    context['todo_status'] = settings.TODO_STATUS_CHOICES
    
    return render(request, "todo/todos-mine-all.html", context)

@login_required()
def todos_shared_in(request):
    # dictionary for initial data with 
    # field names as keys
    context = {}
 
    # add the dictionary during initialization
    item_list = Todo.objects.filter(
        workspace=get_active_workspace(request),
        shared_with=request.user, 
        status=settings.ACTIVE
        )

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj
    
    return render(request, "todo/todos-shared-in.html", context)

@login_required()
def todos_shared_out(request):
    # dictionary for initial data with 
    # field names as keys
    context = {}
 
    # add the dictionary during initialization
    item_list = Todo.objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        Q(status=settings.ACTIVE) &
        Q(user=request.user) & 
        ~Q(shared_with=request.user) & 
        Q(shared_with__isnull=False)
        )

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj
    
    return render(request, "todo/todos-shared-out.html", context)

@login_required()
def todos_archived(request):
    # dictionary for initial data with 
    # field names as keys
    context = {}
 
    # add the dictionary during initialization
    item_list = Todo.objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        Q(status=settings.ARCHIVED) &
        (Q(user=request.user) | Q(shared_with=request.user))
        )

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj
    
    return render(request, "todo/todos-archived.html", context)

@login_required()
def todos_trashed(request):
    # dictionary for initial data with 
    # field names as keys
    context = {}
 
    # add the dictionary during initialization
    item_list = Todo.deleted_objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        (Q(user=request.user) or Q(shared_with=request.user))
        )

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj
    
    return render(request, "todo/todos-trashed.html", context)

@login_required()
def todos_by_user(request, pk):
    # dictionary for initial data with 
    # field names as keys
    context = {}

    user = get_object_or_404(User, pk=pk)

    context['other_user'] = user 

    # add the dictionary during initialization
    item_list = Todo.objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        Q(status=settings.ACTIVE) &
        ((Q(user=user) & Q(shared_with=request.user)) | (Q(user=request.user) & Q(shared_with=user)))
        )

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj
    
    return render(request, "todo/todos-by-user.html", context)

@login_required()
def todo_detail(request, pk):
    todo = get_object_or_404(Todo, pk=pk)    
    comments = todo.comments.all()  # Fetch all comments related to this post
    context = {}
    if request.method == 'POST':
        form = CommentForm(request.POST)
        context['form'] = form
        if form.is_valid():
            comment = form.save(commit=False)
            comment.todo = todo
            comment.author = request.user
            comment.save()

            notification_service = NotificationService()
            
            notifyContext = {
                'actorFirstName': request.user.first_name,
                'todoTitle': todo.title,
                'commentCreationDate': str(comment.created_at),
                'todoDetailLink': str(settings.APP_URL)+str(reverse("todos.detail", args=[todo.id])),
            }

            if (request.user == todo.user) & bool(list(todo.shared_with.all())):
                 for usr in todo.shared_with.all():
                    notification_service.send_notification(user=usr, template_name="todo_comment", context=notifyContext, channels=["in_app", "push"])
            else:
                    notification_service.send_notification(user=todo.user, template_name="todo_comment", context=notifyContext, channels=["in_app", "push"])
            return redirect('todos.detail', pk=todo.pk)
    else:
        context['form'] = CommentForm()
    context['todo']=todo
    context['comments']=comments
    context['media_url']=settings.MEDIA_URL
    context['next']=request.GET.get('next')
    return render(request, 'todo/todo-detail.html', context)

@login_required()
def todo_delete(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    context = {}
    context['todo'] = todo
    if request.method == 'POST':
        todo.delete()
        return redirect(request.GET.get('next'))
    context['next']=request.GET.get('next')
    return render(request, 'todo/todo-confirm-delete.html', context)

@login_required()
def todo_restore(request, pk):
    if request.method == 'POST':
        todo = Todo.deleted_objects.filter(id=pk)
        if todo:
            todo.restore()
            return redirect('todos.trashed')
    return redirect('todos.trashed')

@login_required()
def todo_status_change(request, pk):
    todo = get_object_or_404(Todo, pk=pk)
    if request.method == 'POST':
        oldStatus = todo.todo_status
        newStatus = request.POST.get('todo_status')
        form = TodoStatusChangeForm(request.POST, instance=todo)
        if form.is_valid():
            form.save()
            timelineLog = TodoTimeline()
            timelineLog.todo = todo
            timelineLog.user = request.user
            timelineLog.todo_status = newStatus
            timelineLog.save()

            if int(newStatus) == int(settings.COMPLETED):
                todo.completed_at = datetime.now()
                todo.save()
            
            if (newStatus != oldStatus):

                notification_service = NotificationService()

                notifyContext = {
                    'todoTitle': todo.title,
                    'todoStatus': str(get_choice(settings.TODO_STATUS_CHOICES, todo.todo_status)),
                    'actorFirstName': request.user.first_name,
                    'todoDetailLink': str(settings.APP_URL)+str(reverse("todos.detail", args=[todo.id])),
                }
                if (request.user == todo.user) & bool(list(todo.shared_with.all())):
                    for usr in todo.shared_with.all():
                        notification_service.send_notification(user=usr, template_name="todo_status_change", context=notifyContext, channels=["in_app", "push"])
                elif request.user != todo.user:
                    notification_service.send_notification(user=todo.user, template_name="todo_status_change", context=notifyContext, channels=["in_app", "push"])
                    for usr in todo.shared_with.all().exclude(pk=request.user.id):
                        notification_service.send_notification(user=usr, template_name="todo_status_change", context=notifyContext, channels=["in_app", "push"])
            # context['message']= "Successfully changed the todo Status"
            return redirect(request.POST.get('next'))

@login_required()
def workspace_create(request):
    # dictionary for initial data with 
    # field names as keys
    context = {}
    # add the dictionary during initialization
    if request.method == 'POST':
        form = WorkspaceForm(request.POST)
        if form.is_valid():
            workspace = Workspace()
            workspace.user = request.user
            workspace.name = request.POST.get('name')
            workspace.save()
            # print(len(request.user.active_workspace.all()))
            if len(request.user.active_workspace.all()) == 0:
                # set active workspace in database
                set_active_workspace(request.user, workspace)
            context['message']= "Successfully saved workspace"
            response = render(request, "workspace/workspace-create.html", context)
            return response
        else:
            context['form'] = form
    context['next']=request.GET.get('next')
    response = render(request, "workspace/workspace-create.html", context)
    return response

@login_required()
def workspaces_list(request):
    # dictionary for initial data with 
    # field names as keys
    context = {}
 
    # add the dictionary during initialization
    item_list = Workspace.objects.filter(
        Q(user=request.user) | Q(shared_with=request.user)
        )

    paginator = Paginator(item_list, 5)  # Show 5 items per page.

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context['page_obj'] = page_obj
    
    return render(request, "workspace/workspaces-list.html", context)

@login_required()
def workspace_detail(request, pk):
    workspace = get_object_or_404(Workspace, pk=pk)
    context={}
    context['workspace']=workspace
    context['next']=request.GET.get('next')
    return render(request, 'workspace/workspace-detail.html', context)

@login_required()
def workspace_update(request, pk):
    context = {}
    workspace = get_object_or_404(Workspace, pk=pk)
    context['form'] = WorkspaceForm(instance=workspace)
    context['record_statuses'] = settings.RECORD_STATUS_CHOICES
    if request.method == 'POST':
        form = WorkspaceForm(request.POST, instance=workspace)
        if form.is_valid():
            form.save()
            context['message']= "Successfully saved workspace"
            response = render(request, 'workspace/workspace-create.html', context)
            # set active workspace in database
            set_active_workspace(request.user, workspace)
            return response
    context['next']=request.GET.get('next')
    response = render(request, 'workspace/workspace-create.html', context)
    return response

@login_required()
def workspace_share(request, pk):
    workspace = get_object_or_404(Workspace, pk=pk)
    context = {}
    users = User.objects.exclude(pk=request.user.pk).exclude(pk=workspace.user.pk).exclude(pk__in = workspace.shared_with.only('id'))
    context['workspace'] = workspace
    context['users'] = users
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_to_share = get_object_or_404(User, pk=user_id)
        if user_to_share not in workspace.shared_with.all():
            workspace.shared_with.add(user_to_share)

        notification_service = NotificationService()
        
        notifyContext = {
            'actorFirstName': request.user.first_name,
            'workspaceName': workspace.name,
            'workspaceShareDate': datetime.now(),
            'workspaceDetailLink': str(settings.APP_URL)+str(reverse("workspaces.detail", args=[workspace.id])),
        }
        
        notification_service.send_notification(user=user_to_share, template_name="workspace_share", context=notifyContext, channels=["in_app", "push"])
        
        context['message']= "Successfully shared the Workspace."
    return render(request, 'workspace/workspace-share.html', context)

@login_required()
def workspace_change(request):
    if request.method == 'POST':
        pk = request.POST.get('workspace')
        workspace = get_object_or_404(Workspace, pk=pk)
        if workspace:
            # context['message']= "Successfully changed workspace"
            response = redirect(request.POST.get('next'))
            print(request)
            # set active workspace in database
            set_active_workspace(request.user, workspace)
            return response

@login_required
def search_result(request):
    context = {}
    if ('type' in request.GET) & ('id' in request.GET):
        id = request.GET.get('id')
        type = request.GET.get('type')
        result={}
        if type=='todo':
            result = get_object_or_404(Todo, pk=id)
        elif type=='user':
            result = get_object_or_404(User, pk=id)
        # elif type=='comment':
        #     result = get_object_or_404(Comment, pk=id)
        context['type'] = type
        context['result'] = result
    return render(request, 'search-result.html', context)
        
# ---------- AJAX Views ---------- 
@login_required
def grand_search(request):
    if 'keyword' in request.GET:
        term = request.GET.get('keyword')
        users = User.objects.filter(Q(username__icontains=term) | Q(email__icontains=term) | Q(first_name__icontains=term)).exclude(pk=request.user.pk)
        results = []
        for user in users:
            results.append({
                'type': 'user',
                'id': user.id,
                'label': user.first_name +' '+user.last_name  # label is a jQuery UI-specific key to show in the dropdown
            })
        todos = Todo.objects.filter(Q(title__icontains=term) | Q(body__icontains=term))
        for todo in todos:
            results.append({
                'type': 'todo',
                'id': todo.id,
                'label': todo.title # label is a jQuery UI-specific key to show in the dropdown
            })
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)

@login_required
def get_count_todos(request):
    shared_in = Todo.objects.filter(
        workspace=get_active_workspace(request),
        shared_with=request.user, 
        status=settings.ACTIVE        
        )
    shared_out = Todo.objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        Q(status=settings.ACTIVE) &
        Q(user=request.user) & 
        ~Q(shared_with=request.user) & 
        Q(shared_with__isnull=False)
        )
    pending = Todo.objects.filter(
        Q(workspace=get_active_workspace(request)) & 
        (Q(user=request.user) | Q(shared_with=request.user)) & 
        Q(status=settings.ACTIVE) & 
        Q(todo_status=Todo.PENDING)        
        )
    return JsonResponse({
        'shared_in': shared_in.count(), 
        'shared_out': shared_out.count(), 
        'pending': pending.count()
        })

@login_required
def search_users(request):
    if 'search_term' in request.GET:
        term = request.GET.get('search_term')
        todoId = request.GET.get('todo', None)
        wSpaceId = request.GET.get('workspace', None)
        
        if todoId is not None:
            todo = get_object_or_404(Todo, pk=todoId)
            obj = todo
        elif wSpaceId is not None:
            wspace = get_object_or_404(Workspace, pk=wSpaceId)
            obj = wspace

        users = User.objects.filter(Q(username__icontains=term) | Q(email__icontains=term) | Q(first_name__icontains=term)).exclude(pk=request.user.pk).exclude(pk=obj.user.pk).exclude(pk__in = obj.shared_with.only('id'))
        results = []
        for user in users:
            results.append({
                'id': user.id,
                'label': user.first_name +' '+user.last_name  # label is a jQuery UI-specific key to show in the dropdown
            })
        return JsonResponse(results, safe=False)
    return JsonResponse([], safe=False)

def getFirebaseConfig(request):
    config = {
      'apiKey': settings.FIREBASE_CONFIG['apiKey'],
      'authDomain': settings.FIREBASE_CONFIG['authDomain'],
      'projectId': settings.FIREBASE_CONFIG['projectId'],
      'storageBucket': settings.FIREBASE_CONFIG['storageBucket'],
      'messagingSenderId': settings.FIREBASE_CONFIG['messagingSenderId'],
      'appId': settings.FIREBASE_CONFIG['appId'],
      'measurementId': settings.FIREBASE_CONFIG['measurementId']
    }
    return JsonResponse(config)
class SaveFCMTokenView(APIView):
    # permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        if serializer.is_valid():
            fcm_token = serializer.validated_data['fcm_token']
            profile, created = UserProfile.objects.get_or_create(user=request.user)
            profile.fcm_token = fcm_token
            profile.save()
            return Response({"message": "FCM token saved successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        # Filter notifications to only show those for the logged-in user
        return self.queryset.filter(user=self.request.user, is_read=False)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'Notification marked as read'})

    @staticmethod
    def send_push_notification(user: User, message: str):
        push_service = FCMNotification(api_key=settings.FCM_SERVER_KEY)
        registration_id = user.user_profile.fcm_token  # User's FCM token stored in their profile
        data_message = {"message": message}
        push_service.notify_single_device(registration_id=registration_id, data_message=data_message)

@login_required
def notifications_unread(request):
    notified = Notification.objects.filter(user=request.user, is_read=False)
    context={}
    context['notifications']=notified
    context['next']=request.GET.get('next')
    return render(request, 'notification/notification-list.html', context)

# ---------- Utils ----------
# this @login_required decorator only works if the view function accepts request as an argument 
# @login_required 
def set_active_workspace(user, workspace):
    actWorkspace = ActiveWorkspace.objects.filter(user=user.id)
    if actWorkspace:
        actWorkspace.update(workspace = workspace)
    else:
        actWorkspace = ActiveWorkspace(user = user, workspace = workspace)
        actWorkspace.save()
    return True

@login_required
def get_active_workspace(request):
    actWorkspace = request.user.active_workspace.first()
    if isinstance(actWorkspace, ActiveWorkspace):
        return request.user.active_workspace.first().workspace
    else:
        return False

def get_choice(all_choices, search):
    for choice in all_choices:
        if choice[0] == search:
            return choice[1]
    return None 
# ---
def send_verification_email(user, request):
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    mail_subject = "Verify Your Email Address"
    context = {
        'user': user,
        'domain': current_site.domain,
        'uid': uid,
        'token': token,
    }
    html_content = render_to_string('emails/verification_email.html', context)
    text_content = render_to_string('emails/verification_email.txt', context)

    # Send email
    email_sent = send_email(mail_subject, text_content, [user.email], html_message=html_content)

    if email_sent:
        # If email sent successfully, proceed to next step
        return True
    else:
        # Handle email failure case
        return False
