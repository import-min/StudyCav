import logging
from django.db.models import Exists, OuterRef
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth import logout
from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from .models import StudyGroup, CalendarEvent, Membership, Document, Keyword, UserProfile, JoinRequest, ChatRoom, Message
from django.core.files.storage import default_storage
from .forms import DocumentUploadForm
from django.contrib.auth.decorators import login_required
import requests
from django.http import JsonResponse

def about_page(request):
    return render(request, 'about.html')


@login_required
def get_events(request):
    events = CalendarEvent.objects.all()
    event_list = [
        {
            "title": event.title,
            "start": event.start_time.isoformat(),
            "end": event.end_time.isoformat(),
            "description": event.description,
            "location": event.location,
        }
        for event in events
    ]
    return JsonResponse(event_list, safe=False)




logger = logging.getLogger(__name__)

@login_required
def upload_file(request, group_name):
    group = StudyGroup.objects.filter(name=group_name)
    if group.exists():
        # Get the first matching study group
        study_group = group.first()
    else:
        messages.error(request, "The specified study group does not exist.")
        return redirect('study_group_list')

    # Check if the user is a member of the study group or an admin
    if not (Membership.objects.filter(study_group=study_group, user=request.user).exists() or
            request.user.is_superuser or
            request.user.email in settings.AUTHORIZED_ADMIN_EMAILS):
        messages.error(request, "You must be a member of this study group or an admin to upload files.")
        return redirect('study_group_details', group_id=study_group.id)

    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.study_group = study_group
            document.save()

            # Process keywords entered as a comma-separated string
            keywords_input = form.cleaned_data['keywords']
            if keywords_input:
                keywords_list = [kw.strip() for kw in keywords_input.split(',')]
                for kw in keywords_list:
                    keyword, created = Keyword.objects.get_or_create(name=kw)
                    document.keywords.add(keyword)

            return redirect('group_detail', group_name=group_name)
    else:
        form = DocumentUploadForm()

    return render(request, 'upload_file.html', {'form': form, 'study_group': study_group})

@login_required
def edit_document(request, group_id, document_id):
    study_group = get_object_or_404(StudyGroup, id=group_id)
    document = get_object_or_404(Document, id=document_id, study_group = study_group, user=request.user)
    #only document uploader can edit or delete
    if document.user != request.user:
        return redirect('study_group_details', group_id = group_id)

    if request.method == "POST":
        form = DocumentUploadForm(request.POST, instance=document)
        if form.is_valid():
            document = form.save(commit=False)
                
            # Update keywords
            keywords_input = form.cleaned_data['keywords']
            if keywords_input:
                # Clear old keywords
                document.keywords.clear()
                    
                # Add new keywords
                keywords_list = [kw.strip() for kw in keywords_input.split(',')]
                for kw in keywords_list:
                    keyword, created = Keyword.objects.get_or_create(name=kw)
                    document.keywords.add(keyword)
                
            document.save()
            return redirect('group_detail', group_name=study_group.name)
    else:
        # Prefill keywords as comma-separated names
        keywords = ', '.join(document.keywords.values_list('name', flat=True))
        form = DocumentUploadForm(instance=document, initial={'keywords': keywords})
    return render(request, 'edit_document.html',{
        'form':form,
        'study_group': study_group,
        'document': document
    })

@login_required
def delete_document(request, group_id, document_id):
    study_group = get_object_or_404(StudyGroup, id = group_id)
    # Retrieve the document, ensuring it belongs to the user
    document = get_object_or_404(Document, id=document_id, study_group = study_group, user = request.user)

    if request.method == 'POST':
        document.delete()
        # Redirect back to the study group page after deletion
        return redirect('group_detail', group_name = study_group.name)

    # Render the delete confirmation page
    return render(request, 'delete_document.html', {'document': document, 'study_group': study_group})


@login_required
def group_detail(request, group_name):
    # Get the study group by name
    study_groups = StudyGroup.objects.filter(name=group_name)
    if study_groups.exists():
        study_group = study_groups.first()  # Handle the first result if multiple exist
    else:
        messages.error(request, "The specified study group does not exist.")
        return redirect('study_group_list')

    # Check if the user is a member of the study group or an admin
    if not (Membership.objects.filter(study_group=study_group, user=request.user).exists() or
            request.user.is_superuser or
            request.user.email in settings.AUTHORIZED_ADMIN_EMAILS):
        messages.error(request, "You must be a member of this study group or an admin to view its details.")
        return redirect('study_group_details', group_id=study_group.id)

    # Retrieve documents related to the study group
    documents = Document.objects.filter(study_group=study_group)

    return render(request, 'group_detail.html', {
        'study_group': study_group,
        'documents': documents
    })

from django.utils.timezone import now

@login_required
def study_group_details(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    events = CalendarEvent.objects.filter(study_group=group, end_time__gte=now())
    members = Membership.objects.filter(study_group=group).select_related('user')
    return render(request, 'b04/study_group_details.html', {
        'group': group,
        'events': events,
        'members': members
    })

@login_required
def google_login_callback(request):
    user = request.user
    logger.debug(f"google_login_callback: Logged in user - {user.username}, email - {user.email}")

    if user.email in settings.AUTHORIZED_ADMIN_EMAILS or user.groups.filter(name='PMA Admin').exists():
        logger.debug(f"google_login_callback: {user.email} is an authorized admin, redirecting to admin_dashboard")
        return redirect('admin_dashboard')
    else:
        logger.debug(f"google_login_callback: {user.email} is not an authorized admin, redirecting to common_dashboard")
        return render(request, 'not_authorized.html')

def check_and_login(request):
    # Check if the user is already logged in
    if request.user.is_authenticated:
        # Log out the current user
        logout(request)

    request.session.flush()  # Clear the session
    cache.clear()  # Clear the cache

    # redirect to Google login page (applies to ALL users -> admin or common)
    return redirect('/accounts/google/login/?process=login')


def logout_view(request):
    access_token = request.session.get('access_token')
    if access_token:
        #Revoke
        response = requests.post(
            'https://oauth2.googleapis.com/revoke',
            params={'token': access_token},
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )

    logout(request)
    return redirect('/')


def post_login_redirect(request):
    """Redirects user to the correct dashboard after successful login."""
    user = request.user

    if user.is_authenticated:
        email = user.email

        # Check if the user's email belongs to an admin
        if email in settings.AUTHORIZED_ADMIN_EMAILS:
            return redirect('/admin-dashboard/')
        else:
            return redirect('/common-dashboard/')
    else:
        # If the user is not authenticated, send them to the login page
        return redirect('/login/')

def login_view(request):
    logger.debug("login_view: Entering login view")
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        logger.debug(f"login_view: Attempting login for user - {username}")


        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            logger.debug(f"login_view: Successfully logged in {user.username}")

            # Redirect to the appropriate dashboard
            if user.is_superuser or user.groups.filter(name='PMA Admin').exists():
                logger.debug(f"login_view: Redirecting {user.username} to admin_dashboard")
                return redirect('admin_dashboard')  # Redirect admins to admin dashboard
            else:
                logger.debug(f"login_view: Redirecting {user.username} to common_dashboard")
                return redirect('common_dashboard')  # Redirect regular users to common dashboard
        else:
            logger.debug(f"login_view: Failed login attempt for user - {username}")
            # Invalid login, show error message
            return render(request, 'login.html', {'error': 'Invalid username or password'})

    return render(request, 'login.html')


@login_required
def dashboard(request):
    user = request.user
    logger.debug(f"dashboard: Accessed dashboard by {user.username}")

    # Check if the user is an admin by either superuser status or group membership or authorized email
    if user.is_superuser or user.groups.filter(name='PMA Admin').exists() or user.email in settings.AUTHORIZED_ADMIN_EMAILS:
        logger.debug(f"dashboard: Redirecting {user.username} to admin_dashboard")
        return redirect('admin_dashboard')
    else:
        logger.debug(f"dashboard: Redirecting {user.username} to common_dashboard")
        return redirect('common_dashboard')


def home(request):
    logger.debug("home: Accessed home page")
    study_groups = StudyGroup.objects.all()  # Get all study groups
    context = {
        'study_groups': study_groups,
        'account_name': request.user.username,
    }
    return render(request, 'b04/home.html', context)

def is_admin(user):
    logger.debug(f"is_admin: Checking if {user.username} is admin")
    return user.is_superuser or user.email in settings.AUTHORIZED_ADMIN_EMAILS

def is_common_user(user):
    logger.debug(f"is_common_user: Checking if {user.username} is common user")
    return user.groups.filter(name='Common User').exists() or user.is_authenticated

@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def admin_dashboard(request):
    study_groups = StudyGroup.objects.all()  # Get all study groups
    return render(request, 'admin_dashboard.html', {
        'study_groups': study_groups,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'account_name': request.user.username,
    })


from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import logout
from django.contrib import messages
from .models import StudyGroup, CalendarEvent, Membership, JoinRequest

import logging

logger = logging.getLogger(__name__)

@login_required
@user_passes_test(lambda user: user.is_authenticated)
def common_dashboard(request):
    logger.debug(f"common_dashboard: Accessed common dashboard by {request.user.username}")
    
    # Fetch user's information
    owned_groups = StudyGroup.objects.filter(user=request.user)
    pending_requests = JoinRequest.objects.filter(study_group__in=owned_groups, status='pending')
    first_name = request.user.first_name
    last_name = request.user.last_name
    email = request.user.email
    account_name = email.split("@")[0]

    # Get upcoming events for groups the user is a member of
    memberships = Membership.objects.filter(user=request.user)
    upcoming_events = CalendarEvent.objects.filter(
        study_group__in=[membership.study_group for membership in memberships],
        start_time__gte=timezone.now()
    ).order_by('start_time')

    # Calculate countdowns
    for event in upcoming_events:
        event.countdown = (event.start_time - timezone.now()).days

    context = {
        'first_name': first_name,
        'last_name': last_name,
        'account_name': account_name,
        'pending_requests': pending_requests,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'common_dashboard.html', context)


@login_required
# def join_group(request, group_id):
#     group = get_object_or_404(StudyGroup, id=group_id)
#     Membership.objects.get_or_create(user=request.user, study_group=group)
#     return redirect('study_group_list')  # Redirect back to the study groups list page
@login_required
@login_required
def request_to_join_group(request, group_id):
    study_group = get_object_or_404(StudyGroup, id=group_id)

    # Prevent duplicate requests or membership
    if Membership.objects.filter(user=request.user, study_group=study_group).exists():
        return redirect('study_group_list')
    if JoinRequest.objects.filter(user=request.user, study_group=study_group, status='pending').exists():
        return redirect('study_group_list')

    # Create a new join request
    JoinRequest.objects.create(user=request.user, study_group=study_group, status='pending')
    return redirect('study_group_list')

@login_required
def accept_join_request(request, request_id):
    join_request = get_object_or_404(JoinRequest, id=request_id)

    # Ensure the current user owns the study group
    if join_request.study_group.user != request.user:
        return redirect('common_dashboard')

    Membership.objects.create(user=join_request.user, study_group=join_request.study_group)
    join_request.delete()
    return redirect('common_dashboard')

@login_required
def reject_join_request(request, request_id):
    join_request = get_object_or_404(JoinRequest, id=request_id)

    # Ensure the current user owns the study group
    if join_request.study_group.user != request.user:
        return redirect('common_dashboard')

    # Reject the request: Delete the join request
    join_request.delete()

    return redirect('common_dashboard')


@login_required
def leave_group(request, group_id):
    group = StudyGroup.objects.get(id=group_id)
    Membership.objects.filter(user=request.user, study_group=group).delete()
    return redirect('dashboard')

@login_required
def create_study_group(request):
    if request.method == "POST":
        name = request.POST.get("group_name")
        description = request.POST.get("description")
        date = request.POST.get("date")

        if name and description and date:
            group = StudyGroup.objects.create(name=name, description=description, date=date, user=request.user)
            Membership.objects.create(user=request.user, study_group=group)  # Ensure Membership is created

            return redirect('dashboard')
        else:
            return render(request, 'create_study_group.html', {'error': 'All fields are required'})

    return render(request, 'create_study_group.html')

# View for admin study groups with delete option
@login_required
@user_passes_test(is_admin)
def admin_study_groups(request):
    study_groups = StudyGroup.objects.all()
    return render(request, 'all_study_groups_admin.html', {'study_groups': study_groups})

# View for common users to view study groups without delete option
@login_required
def common_user_study_groups(request):
    study_groups = StudyGroup.objects.all()
    return render(request, 'all_study_groups.html', {'study_groups': study_groups})

@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def delete_study_group(request, group_id):
    study_group = get_object_or_404(StudyGroup, id=group_id)
    study_group.delete()
    messages.success(request, f"Study Group '{study_group.name}' has been deleted.")
    return redirect('admin_dashboard')

@login_required
def calendar_view(request):
    events = CalendarEvent.objects.all()
    return render(request, 'b04/calendar.html', {'events': events})


@login_required
def create_event(request):
    study_groups = StudyGroup.objects.filter(membership__user=request.user)

    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        study_group_id = request.POST.get('study_group')
        location = request.POST.get('location')

        if study_group_id:
            try:
                study_group = StudyGroup.objects.get(id=study_group_id)
                # Create the event
                CalendarEvent.objects.create(
                    user=request.user,
                    title=title,
                    description=description,
                    start_time=start_time,
                    end_time=end_time,
                    study_group=study_group,
                    location=location
                )
                return redirect('common_dashboard')
            except StudyGroup.DoesNotExist:
                messages.error(request, "Study group not found.")
        else:
            messages.error(request, "Please select a study group.")

    return render(request, 'b04/create_event.html', {'study_groups': study_groups})
@login_required
def study_group_list(request):
    user = request.user
    user_memberships = request.user.membership_set.all()
    user_groups = StudyGroup.objects.filter(membership__in=user_memberships)
    other_groups = StudyGroup.objects.exclude(id__in=user_groups.values_list('id', flat=True))

       # Annotate other_groups with pending join request information
    pending_requests = JoinRequest.objects.filter(user=user, study_group=OuterRef('pk'), status='pending')
    other_groups = StudyGroup.objects.exclude(id__in=user_groups.values_list('id', flat=True)).annotate(
        has_pending_request=Exists(pending_requests)
    )

    return render(request, 'b04/all_study_groups.html', {
        'user_groups': user_groups,
        'other_groups': other_groups,
    })

@login_required
def delete_group(request, group_id):
    study_group = get_object_or_404(StudyGroup, id=group_id)
    if request.user == study_group.user:  # uses the `user` field as owner
        if request.method == 'POST':
            study_group.delete()
            return redirect('common_dashboard')
        return render(request, 'confirm_delete_group.html', {'study_group': study_group})
    else:
        return redirect('study_group_details', group_id=group_id)

@login_required
@user_passes_test(is_admin)
def adminView_study_group_details(request, study_group_id):
    study_group = get_object_or_404(StudyGroup, id=study_group_id)
    events = CalendarEvent.objects.filter(study_group=study_group)
    members = Membership.objects.filter(study_group=study_group).select_related('user')
    documents = Document.objects.filter(study_group=study_group)

    context = {
        'group': study_group,
        'events': events,
        'members': members,
        'documents': documents,
    }
    return render(request, 'b04/adminView_study_group_details.html', context)

@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def adminView_group_detail(request, group_id):
    study_group = get_object_or_404(StudyGroup, id=group_id)
    documents = study_group.documents.all()
    context = {
        'study_group': study_group,
        'documents': documents,
    }
    return render(request, 'b04/adminView_group_detail.html', context)


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def adminView_delete_document(request, group_id, document_id):
    # Retrieve the study group
    study_group = get_object_or_404(StudyGroup, id=group_id)

    # Retrieve the document from the study group
    document = get_object_or_404(Document, id=document_id, study_group=study_group)

    if request.method == 'POST':
        # Delete the document
        document.delete()

        # Redirect to the admin view of the study group details
        return redirect('adminView_study_group_details', study_group_id=study_group.id)

    # Render the delete confirmation page for admins
    return render(request, 'adminView_delete_document.html', {'document': document, 'study_group': study_group})


@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def remove_member(request, study_group_id, member_id):
    # Get the study group and the membership
    study_group = get_object_or_404(StudyGroup, id=study_group_id)
    membership = get_object_or_404(Membership, id=member_id, study_group=study_group)

    if membership.user == request.user:
        return HttpResponseForbidden("You cannot remove yourself from the group.")

    if membership.user.groups.filter(name='Admin').exists():
        return HttpResponseForbidden("You cannot remove an admin from the group.")

    # Remove the member
    membership.delete()

    # Redirect to the study group details page
    return redirect('adminView_study_group_details', study_group_id=study_group.id)

@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def delete_event(request, study_group_id, event_id):
    # Retrieve the study group
    study_group = get_object_or_404(StudyGroup, id=study_group_id)

    # Retrieve the event from the study group
    event = get_object_or_404(CalendarEvent, id=event_id, study_group=study_group)

    # Only process POST requests
    if request.method == 'POST':
        # Delete the event
        event.delete()
        messages.success(request, "Event deleted successfully.")

    # Redirect to the admin view of the study group details
    return redirect('adminView_study_group_details', study_group_id=study_group.id)

@login_required
def chat_room_view(request, group_id):
    # Get the study group and check if the user is a member or admin
    study_group = get_object_or_404(StudyGroup, id=group_id)

    # Check if the user is a member of the study group or an admin
    if not (Membership.objects.filter(study_group=study_group, user=request.user).exists() or
            request.user.is_superuser or
            request.user.email in settings.AUTHORIZED_ADMIN_EMAILS):
        messages.error(request, "You must be a member of this study group or an admin to access the chat.")
        return redirect('study_group_details', group_id=group_id)    # Redirect if not a member or admin

    # Get the associated chat room
    chat_room = study_group.chat_room

    # Handle new messages from the user
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(user=request.user, study_group=study_group, chat_room=chat_room, content=content)
            messages.success(request, "Your message has been sent.")

    # Get messages for the chat room (ordering by timestamp)
    messages_in_chat = chat_room.get_messages()

    return render(request, 'chat_room.html', {
        'study_group': study_group,
        'messages': messages_in_chat,
    })

@login_required
@user_passes_test(is_admin, login_url='/accounts/login/')
def adminView_chat_room_view(request, group_id):
    # Get the study group and check if the user is a member or admin
    study_group = get_object_or_404(StudyGroup, id=group_id)

    # Check if the user is a member of the study group or an admin
    if not (Membership.objects.filter(study_group=study_group, user=request.user).exists() or
            request.user.is_superuser or
            request.user.email in settings.AUTHORIZED_ADMIN_EMAILS):
        messages.error(request, "You must be a member of this study group or an admin to access the chat.")
        return redirect('adminView_group_detail', group_name=study_group.name)  # Redirect if not a member or admin

    # Get the associated chat room
    chat_room = study_group.chat_room

    # Handle new messages from the user
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(user=request.user, study_group=study_group, chat_room=chat_room, content=content)
            messages.success(request, "Your message has been sent.")

    # Get messages for the chat room (ordering by timestamp)
    messages_in_chat = chat_room.get_messages()

    return render(request, 'adminView_chat_room.html', {
        'study_group': study_group,
        'messages': messages_in_chat,
    })

@login_required
def delete_message(request, study_group_id, message_id):
    # Get the message object by ID
    message = get_object_or_404(Message, id=message_id)

    # Check if the logged-in user is the one who posted the message, the owner of the study group, or an admin
    if message.user == request.user or message.study_group.user == request.user or request.user.is_superuser or request.user.email in settings.AUTHORIZED_ADMIN_EMAILS:
        # Delete the message
        message.delete()

    # Redirect back to the appropriate chat room view based on user role
    if request.user.is_superuser or request.user.email in settings.AUTHORIZED_ADMIN_EMAILS:
        return redirect('adminView_chat_room_view', group_id=study_group_id)
    else:
        return redirect('chat_room_view', group_id=study_group_id)
