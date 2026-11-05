
from django.db import models
from django.contrib.auth.models import User


# Teacher and Student Profiles
class Profile(models.Model):

    ROLE_CHOICES = [
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES
    )

    def __str__(self):
        return f"{self.user.username} - {self.role}"


# Assignment Details
class Assignment(models.Model):

    title = models.CharField(max_length=200)

    description = models.TextField()

    due_date = models.DateTimeField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_assignments'
    )

    file = models.FileField(
        upload_to='assignments/',
        blank=True,
        null=True,
        help_text='Assignment instruction document or rubric (PDF)'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# Student Submissions
class Submission(models.Model):

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    file = models.FileField(
        upload_to='submissions/'
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    marks = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    feedback = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['assignment', 'student'],
                name='unique_student_assignment_submission'
            )
        ]

    def __str__(self):
        return f"{self.student.username} - {self.assignment.title}"
