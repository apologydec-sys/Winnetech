from .models import TeacherProfile


def admin_context(request):
    """Adds pending teacher count to all admin templates."""
    if request.user.is_authenticated and request.user.is_staff:
        pending_count = TeacherProfile.objects.filter(is_approved=False).count()
        return {'pending_count': pending_count}
    return {}
