from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role != 'student':
            messages.error(request, "Access restricted. This page is only accessible to students.")
            if profile and profile.role == 'teacher':
                return redirect('teacher_dashboard')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        profile = getattr(request.user, 'profile', None)
        if not profile or profile.role != 'teacher':
            messages.error(request, "Access restricted. This page is only accessible to teachers.")
            if profile and profile.role == 'student':
                return redirect('student_dashboard')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
