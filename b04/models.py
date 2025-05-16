from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class StudyGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_groups') #owner
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    location = models.CharField(max_length=100, blank=True)
    #owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_groups')

    def __str__(self):
        return self.name
    
class Keyword(models.Model):
    name = models.CharField(max_length=50, unique=True)
class Document(models.Model):
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='documents')
    upload = models.FileField(upload_to='documents/')
    upload_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title =models.CharField(max_length = 100, blank = True)
    description=models.CharField(max_length = 200, blank = True)
    keywords = models.ManyToManyField(Keyword, related_name='documents', blank=True)

    def __str__(self):
        return f"{self.upload.name} uploaded by {self.user.username}"

class Membership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.study_group.name}"

# UserProfile model for user roles
class UserProfile(models.Model):
    USER_ROLES = (
        ('common', 'Common User'),
        ('admin', 'PMA Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=USER_ROLES, default='common')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.user.username

# CalendarEvent model for calendar events
class CalendarEvent(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    study_group = models.ForeignKey('StudyGroup', on_delete=models.CASCADE, null=True, blank=True)  # Link to StudyGroup
    location = models.CharField(max_length=255, default="Main Library")
    def __str__(self):
        return self.title

#Request model for requesting to join study group
class JoinRequest(models.Model):
    REQUEST_STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='join_requests')
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='join_requests')
    status = models.CharField(max_length=10, choices=REQUEST_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

class ChatRoom(models.Model):
    study_group = models.OneToOneField(StudyGroup, on_delete=models.CASCADE, related_name="chat_room")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat Room for {self.study_group.name}"

    def get_messages(self):
        return self.messages.all()


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    study_group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    chat_room = models.ForeignKey(ChatRoom, related_name="messages", on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.user.username} in {self.study_group.name}"

    class Meta:
        ordering = ['timestamp']


# Signal to create chatroom when study group is created
@receiver(post_save, sender=StudyGroup)
def create_chat_room(sender, instance, created, **kwargs):
    if created:
        ChatRoom.objects.create(study_group=instance)


# Signal to save chatroom when study group is saved
@receiver(post_save, sender=StudyGroup)
def save_chat_room(sender, instance, **kwargs):
    if instance.chat_room:
        instance.chat_room.save()