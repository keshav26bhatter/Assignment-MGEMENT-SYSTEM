from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from assignments.models import Profile, Assignment


class AssignmentSystemAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a teacher user
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher1@example.com',
            password='Password123!',
            first_name='Prof',
            last_name='Oak'
        )
        Profile.objects.create(user=self.teacher_user, role='teacher')

        # Create a student user
        self.student_user = User.objects.create_user(
            username='student1',
            email='student1@example.com',
            password='Password123!',
            first_name='Ash',
            last_name='Ketchum'
        )
        Profile.objects.create(user=self.student_user, role='student')

    def test_student_registration_success(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Misty Waterflower',
            'username': 'misty',
            'email': 'misty@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        })
        self.assertRedirects(response, reverse('login'))
        user = User.objects.get(username='misty')
        self.assertEqual(user.first_name, 'Misty')
        self.assertEqual(user.last_name, 'Waterflower')
        self.assertTrue(user.check_password('Password123!'))
        self.assertEqual(user.profile.role, 'student')

    def test_registration_validation_duplicate_username(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Duplicate User',
            'username': 'student1',
            'email': 'new_email@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'username', 'A user with this username already exists.')

    def test_registration_validation_duplicate_email(self):
        response = self.client.post(reverse('register'), {
            'full_name': 'Duplicate Email',
            'username': 'newuser',
            'email': 'student1@example.com',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', 'An account with this email address already exists.')


    def test_student_login_and_redirect(self):
        response = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_teacher_login_and_redirect(self):
        response = self.client.post(reverse('login'), {
            'username': 'teacher1',
            'password': 'Password123!'
        })
        self.assertRedirects(response, reverse('teacher_dashboard'))

    def test_invalid_login_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'student1',
            'password': 'WrongPassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid username or password')

    def test_role_based_access_student_cannot_access_teacher_dashboard(self):
        self.client.login(username='student1', password='Password123!')
        response = self.client.get(reverse('teacher_dashboard'))
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_role_based_access_teacher_cannot_access_student_dashboard(self):
        self.client.login(username='teacher1', password='Password123!')
        response = self.client.get(reverse('student_dashboard'))
        self.assertRedirects(response, reverse('teacher_dashboard'))

    def test_unauthenticated_access_redirects_to_login(self):
        student_dash_res = self.client.get(reverse('student_dashboard'))
        self.assertRedirects(student_dash_res, reverse('login'))

        teacher_dash_res = self.client.get(reverse('teacher_dashboard'))
        self.assertRedirects(teacher_dash_res, reverse('login'))

    def test_logout(self):
        self.client.login(username='student1', password='Password123!')
        response = self.client.get(reverse('logout'))
        self.assertRedirects(response, reverse('login'))
        # Ensure session is logged out
        dashboard_res = self.client.get(reverse('student_dashboard'))
        self.assertRedirects(dashboard_res, reverse('login'))
