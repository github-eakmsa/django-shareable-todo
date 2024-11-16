
from django.conf import settings
from app_todo.models import Workspace

# ---
def workspaces(request):
    myWorkspaces = Workspace.objects.filter(user=request.user.id)
    sharedWorkspaces = Workspace.objects.filter(shared_with=request.user.id, status=settings.ACTIVE)
    
    currentWorkspace = {}
    if hasattr(request.user, 'active_workspace'):
        currUser = request.user
        if currUser.active_workspace.first():
            activeWorkspace = request.user.active_workspace.first().workspace
            currentWorkspace = activeWorkspace

    return {
        'MY_WORKSPACES': myWorkspaces, 
        'SHARED_WORKSPACES': sharedWorkspaces, 
        'CURRENT_WORKSPACE': currentWorkspace, 
        }
