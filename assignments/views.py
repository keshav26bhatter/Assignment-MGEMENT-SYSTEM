from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .forms import StudentRegistrationForm, LoginForm, AssignmentForm, SubmissionForm, EvaluationForm
from .models import Assignment, Submission, Profile
from .decorators import student_required, teacher_required
from .activity_logger import log_activity


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def register_view(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'teacher':
            return redirect('teacher_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_activity(user.id, 'STUDENT_REGISTER', f'Registered username: {user.username}', get_client_ip(request))
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentRegistrationForm()

    return render(request, 'assignments/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, 'profile', None)
        if profile and profile.role == 'teacher':
            return redirect('teacher_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                ip = get_client_ip(request)
                profile = getattr(user, 'profile', None)
                if profile and profile.role == 'teacher':
                    log_activity(user.id, 'TEACHER_LOGIN', f'Teacher logged in: {user.username}', ip)
                    return redirect('teacher_dashboard')
                elif profile and profile.role == 'student':
                    log_activity(user.id, 'STUDENT_LOGIN', f'Student logged in: {user.username}', ip)
                    return redirect('student_dashboard')
                else:
                    if user.is_staff or user.is_superuser:
                        log_activity(user.id, 'ADMIN_LOGIN', f'Admin logged in: {user.username}', ip)
                        return redirect('/admin/')
                    messages.error(request, 'Your account does not have an assigned role. Please contact administrator.')
                    logout(request)
                    return redirect('login')
            else:
                messages.error(request, 'Invalid username or password. Please try again.')
    else:
        form = LoginForm()

    return render(request, 'assignments/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_activity(request.user.id, 'USER_LOGOUT', f'User logged out: {request.user.username}', get_client_ip(request))
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


# ==========================================
# TEACHER VIEWS
# ==========================================

@teacher_required
def teacher_dashboard(request):
    user = request.user
    assignments = Assignment.objects.filter(created_by=user).order_by('-created_at')

    total_assignments = assignments.count()
    total_submissions = Submission.objects.filter(assignment__created_by=user).count()

    now = timezone.now()
    upcoming_deadlines = assignments.filter(due_date__gte=now).order_by('due_date')[:5]
    recent_assignments = assignments[:10]

    context = {
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'upcoming_deadlines': upcoming_deadlines,
        'recent_assignments': recent_assignments,
    }
    return render(request, 'assignments/teacher_dashboard.html', context)


@teacher_required
def assignment_create(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            log_activity(request.user.id, 'ASSIGNMENT_CREATED', f'Created assignment: {assignment.title}', get_client_ip(request))
            messages.success(request, f'Assignment "{assignment.title}" created successfully.')
            return redirect('teacher_dashboard')
    else:
        form = AssignmentForm()

    return render(request, 'assignments/assignment_form.html', {'form': form, 'title': 'Create New Assignment'})


@teacher_required
def assignment_edit(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, instance=assignment)
        if form.is_valid():
            form.save()
            log_activity(request.user.id, 'ASSIGNMENT_UPDATED', f'Updated assignment: {assignment.title}', get_client_ip(request))
            messages.success(request, f'Assignment "{assignment.title}" updated successfully.')
            return redirect('teacher_dashboard')
    else:
        form = AssignmentForm(instance=assignment)

    return render(request, 'assignments/assignment_form.html', {'form': form, 'title': 'Edit Assignment', 'assignment': assignment})


@teacher_required
def assignment_delete(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    if request.method == 'POST':
        title = assignment.title
        assignment.delete()
        log_activity(request.user.id, 'ASSIGNMENT_DELETED', f'Deleted assignment: {title}', get_client_ip(request))
        messages.success(request, f'Assignment "{title}" was successfully deleted.')
        return redirect('teacher_dashboard')
    return render(request, 'assignments/assignment_confirm_delete.html', {'assignment': assignment})


@teacher_required
def assignment_submissions(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk, created_by=request.user)
    submissions = assignment.submissions.select_related('student', 'student__profile').order_by('-submitted_at')
    return render(request, 'assignments/teacher_submissions.html', {
        'assignment': assignment,
        'submissions': submissions
    })


@teacher_required
def evaluate_submission(request, pk):
    submission = get_object_or_404(Submission, pk=pk, assignment__created_by=request.user)
    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            log_activity(request.user.id, 'ASSIGNMENT_EVALUATED', f'Graded submission id={submission.id} for student {submission.student.username}', get_client_ip(request))
            messages.success(request, f'Evaluation saved for student {submission.student.get_full_name() or submission.student.username}.')
            return redirect('assignment_submissions', pk=submission.assignment.id)
    else:
        form = EvaluationForm(instance=submission)

    return render(request, 'assignments/evaluate_submission.html', {
        'submission': submission,
        'form': form
    })


# ==========================================
# STUDENT VIEWS
# ==========================================

@student_required
def student_dashboard(request):
    user = request.user
    all_assignments = Assignment.objects.all().order_by('-created_at')
    total_available = all_assignments.count()

    # User's submissions mapping
    user_submissions = {s.assignment_id: s for s in Submission.objects.filter(student=user)}
    total_submitted = len(user_submissions)
    pending_count = max(0, total_available - total_submitted)

    now = timezone.now()
    upcoming_deadlines = Assignment.objects.filter(due_date__gte=now).order_by('due_date')[:5]

    assignment_list = []
    for a in all_assignments:
        sub = user_submissions.get(a.id)
        assignment_list.append({
            'assignment': a,
            'is_submitted': sub is not None,
            'submission': sub,
            'is_overdue': a.due_date < now if a.due_date else False,
        })

    context = {
        'total_available': total_available,
        'total_submitted': total_submitted,
        'pending_count': pending_count,
        'upcoming_deadlines': upcoming_deadlines,
        'assignment_list': assignment_list,
    }
    return render(request, 'assignments/student_dashboard.html', context)


@student_required
def student_assignment_detail(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    now = timezone.now()
    is_overdue = assignment.due_date < now if assignment.due_date else False

    if request.method == 'POST' and not submission:
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.assignment = assignment
            sub.student = request.user
            sub.save()
            log_activity(request.user.id, 'ASSIGNMENT_SUBMITTED', f'Submitted assignment: {assignment.title}', get_client_ip(request))
            messages.success(request, 'Your assignment has been submitted successfully!')
            return redirect('student_assignment_detail', pk=assignment.id)
    else:
        form = SubmissionForm() if not submission else None

    return render(request, 'assignments/student_assignment_detail.html', {
        'assignment': assignment,
        'submission': submission,
        'form': form,
        'is_overdue': is_overdue,
    })
