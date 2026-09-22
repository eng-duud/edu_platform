from .models import Enrollment


def academic_context(request):

    context = {
        'user_role': 'guest',
        'is_doctor': False,
        'is_student': False,
        'pending_requests_count': 0,
        'specialization': None,
        'student_level': None,
    }

    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return context

    # Check for Doctor Profile
    try:
        if hasattr(user, 'doctor_profile'):
            context['user_role'] = 'doctor'
            context['is_doctor'] = True
            context['specialization'] = user.doctor_profile.specialization
            try:
                context['pending_requests_count'] = Enrollment.objects.filter(
                    course__doctor=user.doctor_profile,
                    status=Enrollment.Status.PENDING
                ).count()
            except Exception:
                context['pending_requests_count'] = 0

        # Check for Student Profile
        elif hasattr(user, 'student_profile'):
            context['user_role'] = 'student'
            context['is_student'] = True
            context['specialization'] = user.student_profile.specialization
            context['student_level'] = user.student_profile.level
            try:
                context['pending_requests_count'] = Enrollment.objects.filter(
                    student=user.student_profile,
                    status=Enrollment.Status.PENDING
                ).count()
            except Exception:
                context['pending_requests_count'] = 0

        elif user.is_staff or user.is_superuser:
            # Fallback for admin users accessing views
            context['user_role'] = 'doctor'
            context['is_doctor'] = True
    except Exception:
        if user.is_staff or user.is_superuser:
            context['user_role'] = 'doctor'
            context['is_doctor'] = True

    return context
