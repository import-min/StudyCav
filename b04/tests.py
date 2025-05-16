# add tests here

# add tests here
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile, StudyGroup, CalendarEvent, Document, Membership
from django.core.files.uploadedfile import SimpleUploadedFile

class UserProfileModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='testuser', password='testpassword')

        # create if doesn't exist
        cls.profile, created = UserProfile.objects.get_or_create(user=cls.user, defaults={'bio': "Test bio"})

    def test_common_user_default(self):
        self.assertEqual(self.profile.role, "common")

    def test_user_profile_str(self):
        self.assertEqual(str(self.profile), self.user.username)

    def test_user_profile_creation(self):
        self.assertTrue(isinstance(self.profile, UserProfile))
        self.assertEqual(self.profile.user.username, 'testuser')



class StudyGroupModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='testuser')

    def test_create_group(self):
        myGroup = StudyGroup.objects.create(user=self.user, name="Testing Group", description="Creating to test", date="2024-10-30T10:00:00Z", location="Rice 302")
        self.assertIsInstance(myGroup, StudyGroup)

    def test_no_description(self):
        myGroup = StudyGroup.objects.create(user=self.user, name="No Description Group", date="2024-10-30T10:00:00Z")
        self.assertEqual(myGroup.description, "")

    def test_str_method(self):
        group = StudyGroup.objects.create(user=self.user, name="String Rep Group",date="2024-10-30T10:00:00Z")
        self.assertEqual(str(group), "String Rep Group")



class DocumentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="docuser")
        self.group = StudyGroup.objects.create(user=self.user, name="Documents Study Group", date="2024-10-30T10:00:00Z")

    def test_upload(self):
        document = Document.objects.create(study_group=self.group, user=self.user, upload=SimpleUploadedFile("file.txt", b"content"))
        self.assertIsInstance(document, Document)

    def test_str(self):
        document = Document.objects.create(study_group=self.group, user=self.user, upload=SimpleUploadedFile("file.txt", b"content"))
        self.assertEqual(str(document), "documents/file.txt uploaded by docuser")



class CalendarEventModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="caluser")
        self.group = StudyGroup.objects.create(user=self.user, name="Event Group", date="2024-10-30T10:00:00Z")

    def test_create_calendar(self):
        event = CalendarEvent.objects.create(title="Test Event", description="Testing creation capability.", start_time="2024-10-30T10:00:00Z", end_time="2024-10-30T11:00:00Z", user=self.user, study_group=self.group)
        self.assertEqual(event.title, "Test Event")

    def test_event_link_study_group(self):
        event = CalendarEvent.objects.create(title="Event with Study Group A", description="Testing to see if calender event is linked to study group",start_time="2024-10-30T10:00:00Z", end_time="2024-10-30T11:00:00Z", user=self.user, study_group=self.group)
        self.assertEqual(event.study_group, self.group)


#integration tests with the views.py
class DashboardViewTest(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(username="adminUser", password="adminPass", email="admin@example.com")
        self.admin_user.is_superuser = True
        self.admin_user.save()
        self.regular_user = User.objects.create_user(username="commonUser", password="commonPass", email="user@example.com")

    def test_dashboard_admin(self):
        self.client.login(username="adminUser", password="adminPass")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)  #dashboard

    def test_dashboard_regular_user(self):
        self.client.login(username="commonUser", password="commonPass")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)  #common dashboard


class LoginViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testUser", password="testPass")

    def test_login_auth(self):
        self.client.login(username="testUser", password="testPass")
        response = self.client.get(reverse("check_and_login"))
        self.assertEqual(response.status_code, 302)  # log in



'''
class GoogleLoginTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='googleuser', email='user@gmail.com', password='password123')

    def test_google_login_redirect(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('common_dashboard.html'))  # Replace with your view name
        user = response.wsgi_request.user

        self.assertTrue(user.is_authenticated)
        self.assertEqual(response.status_code, 200)
'''