from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponseNotAllowed

from .models import Specialization, Level, Course, Lecture, Enrollment
from .forms import LoginForm, RegistrationForm, LectureForm


# ==============================================================================
# ==============================================================================

def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")
        if hasattr(request.user, 'doctor_profile') or request.user.is_superuser or request.user.is_staff:
            return view_func(request, *args, **kwargs)
        messages.error(request, "هذه الصفحة مخصصة لأعضاء هيئة التدريس فقط.")
        return render(request, '403.html', status=403)
    return _wrapped_view


def student_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")
        if hasattr(request.user, 'student_profile') or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, "هذه الصفحة مخصصة للطلاب المسجلين.")
        return render(request, '403.html', status=403)
    return _wrapped_view


# ==============================================================================
# عام والمصادقة (General & Auth)
# ==============================================================================

def home_redirect(request):
    """توجيه المستخدم للصفحة المناسبة حسب نوع حسابه"""
    if not request.user.is_authenticated:
        return redirect('login')
    if hasattr(request.user, 'doctor_profile') or request.user.is_staff:
        return redirect('doctor_dashboard')
    if hasattr(request.user, 'student_profile'):
        return redirect('student_dashboard')
    return redirect('login')


def user_login(request):
    if request.user.is_authenticated:
        return home_redirect(request)

    form = LoginForm(request.POST or None)
    error_message = None

    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"أهلاً وسهلاً بك، {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            return redirect(next_url or 'home')
        else:
            errors = form.non_field_errors()
            if errors:
                error_message = errors[0]

    return render(request, 'registration/login.html', {
        'form': form,
        'error_message': error_message,
    })


def user_register(request):
    if request.user.is_authenticated:
        return home_redirect(request)

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        if form.cleaned_data.get('user_type') == 'doctor':
            messages.warning(request, "تم إنشاء الحساب بنجاح! يتطلب الحساب مراجعة واعتماد الإدارة.")
            return redirect('login')
        else:
            auth_login(request, user)
            messages.success(request, f"مرحباً بك يا {user.get_full_name() or user.username}! تم إنشاء حسابك بنجاح.")
            return redirect('student_dashboard')

    return render(request, 'registration/register.html', {
        'form': form,
        'specializations': Specialization.objects.all(),
        'levels': Level.objects.all().order_by('specialization', 'number'),
    })


def user_logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
        messages.info(request, "تم تسجيل الخروج بنجاح.")
    return redirect('login')


def preview_phase1(request):
    return render(request, 'preview_phase1.html')


# ==============================================================================
# بوابة الدكتور (Doctor Portal)
# ==============================================================================

@doctor_required
def doctor_dashboard(request):
    doctor = getattr(request.user, 'doctor_profile', None)
    
    if doctor:
        courses = Course.objects.filter(doctor=doctor).order_by('-created_at')
        enrollments = Enrollment.objects.filter(course__doctor=doctor)
        lectures_count = Lecture.objects.filter(course__doctor=doctor).count()
    else:
        courses = Course.objects.all().order_by('-created_at')
        enrollments = Enrollment.objects.all()
        lectures_count = Lecture.objects.count()

    pending_requests = enrollments.filter(status=Enrollment.Status.PENDING).order_by('-requested_at')
    total_students = enrollments.filter(status=Enrollment.Status.APPROVED).values('student').distinct().count()

    return render(request, 'doctor/dashboard.html', {
        'courses': courses,
        'courses_count': courses.count(),
        'total_students_count': total_students,
        'pending_requests_count': pending_requests.count(),
        'total_lectures_count': lectures_count,
        'pending_enrollments': pending_requests[:5],
        'enrollment_requests': pending_requests[:5],
    })


@doctor_required
def doctor_courses(request):
    doctor = getattr(request.user, 'doctor_profile', None)
    courses = Course.objects.filter(doctor=doctor) if doctor else Course.objects.all()
    courses = courses.order_by('-created_at')

    paginator = Paginator(courses, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'doctor/courses.html', {
        'courses': page_obj,
        'page_obj': page_obj,
    })


@doctor_required
def doctor_course_detail(request, course_id):
    doctor = getattr(request.user, 'doctor_profile', None)
    if doctor:
        course = get_object_or_404(Course, id=course_id, doctor=doctor)
    else:
        course = get_object_or_404(Course, id=course_id)

    lectures = course.lectures.all().order_by('number')
    return render(request, 'doctor/course_detail.html', {
        'course': course,
        'lectures': lectures,
    })


@doctor_required
def doctor_lecture_add(request, course_id):
    doctor = getattr(request.user, 'doctor_profile', None)
    course = get_object_or_404(Course, id=course_id, doctor=doctor) if doctor else get_object_or_404(Course, id=course_id)

    form = LectureForm(request.POST or None, request.FILES or None, course=course)
    if request.method == 'POST' and form.is_valid():
        lecture = form.save()
        messages.success(request, f"تمت إضافة المحاضرة '{lecture.title}' بنجاح.")
        return redirect('doctor_course_detail', course_id=course.id)

    return render(request, 'doctor/lecture_form.html', {
        'course': course,
        'form': form,
        'lecture': None,
    })


@doctor_required
def doctor_lecture_edit(request, course_id, lecture_id):
    doctor = getattr(request.user, 'doctor_profile', None)
    course = get_object_or_404(Course, id=course_id, doctor=doctor) if doctor else get_object_or_404(Course, id=course_id)
    lecture = get_object_or_404(Lecture, id=lecture_id, course=course)

    form = LectureForm(request.POST or None, request.FILES or None, instance=lecture, course=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"تم تحديث المحاضرة '{lecture.title}' بنجاح.")
        return redirect('doctor_course_detail', course_id=course.id)

    return render(request, 'doctor/lecture_form.html', {
        'course': course,
        'lecture': lecture,
        'form': form,
    })


@doctor_required
def doctor_lecture_delete(request, course_id, lecture_id):
    doctor = getattr(request.user, 'doctor_profile', None)
    course = get_object_or_404(Course, id=course_id, doctor=doctor) if doctor else get_object_or_404(Course, id=course_id)
    lecture = get_object_or_404(Lecture, id=lecture_id, course=course)

    if request.method == 'POST':
        lecture.delete()
        messages.success(request, "تم حذف المحاضرة بنجاح.")
        return redirect('doctor_course_detail', course_id=course.id)

    return render(request, 'doctor/lecture_confirm_delete.html', {
        'course': course,
        'lecture': lecture,
    })


@doctor_required
def doctor_enrollment_requests(request):
    doctor = getattr(request.user, 'doctor_profile', None)
    base_qs = Enrollment.objects.filter(course__doctor=doctor) if doctor else Enrollment.objects.all()

    status_filter = request.GET.get('status')
    if status_filter in [Enrollment.Status.PENDING, Enrollment.Status.APPROVED, Enrollment.Status.REJECTED]:
        requests_qs = base_qs.filter(status=status_filter)
    else:
        requests_qs = base_qs

    requests_qs = requests_qs.select_related('student', 'student__user', 'course').order_by('-requested_at')
    paginator = Paginator(requests_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'doctor/enrollment_requests.html', {
        'enrollment_requests': page_obj,
        'page_obj': page_obj,
        'pending_count': base_qs.filter(status=Enrollment.Status.PENDING).count(),
    })


@doctor_required
def doctor_enrollment_approve(request, request_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    doctor = getattr(request.user, 'doctor_profile', None)
    enrollment = get_object_or_404(Enrollment, id=request_id, course__doctor=doctor) if doctor else get_object_or_404(Enrollment, id=request_id)

    enrollment.status = Enrollment.Status.APPROVED
    enrollment.decided_at = timezone.now()
    enrollment.save()

    messages.success(request, f"تم قبول انضمام الطالب في مقرر {enrollment.course.name}.")
    return redirect(request.META.get('HTTP_REFERER') or 'doctor_enrollment_requests')


@doctor_required
def doctor_enrollment_reject(request, request_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    doctor = getattr(request.user, 'doctor_profile', None)
    enrollment = get_object_or_404(Enrollment, id=request_id, course__doctor=doctor) if doctor else get_object_or_404(Enrollment, id=request_id)

    enrollment.status = Enrollment.Status.REJECTED
    enrollment.decided_at = timezone.now()
    enrollment.save()

    messages.warning(request, f"تم رفض طلب الانضمام لمقرر {enrollment.course.name}.")
    return redirect(request.META.get('HTTP_REFERER') or 'doctor_enrollment_requests')


@doctor_required
def doctor_profile(request):
    return render(request, 'doctor/profile.html')


# ==============================================================================
# بوابة الطالب (Student Portal)
# ==============================================================================

@student_required
def student_dashboard(request):
    student = getattr(request.user, 'student_profile', None)
    
    if student:
        approved_enrollments = Enrollment.objects.filter(
            student=student,
            status=Enrollment.Status.APPROVED
        ).select_related('course', 'course__doctor', 'course__specialization').order_by('-decided_at')
        enrolled_courses = [e.course for e in approved_enrollments]
        pending_count = Enrollment.objects.filter(student=student, status=Enrollment.Status.PENDING).count()
    else:
        enrolled_courses = []
        pending_count = 0

    return render(request, 'student/dashboard.html', {
        'enrolled_courses': enrolled_courses,
        'my_courses_count': len(enrolled_courses),
        'pending_requests_count': pending_count,
    })


@student_required
def student_courses(request):
    student = getattr(request.user, 'student_profile', None)
    query = request.GET.get('q', '').strip()

    courses_qs = Course.objects.select_related('doctor', 'doctor__user', 'specialization', 'level')
    if student:
        courses_qs = courses_qs.filter(specialization=student.specialization)
        if student.level:
            courses_qs = courses_qs.filter(level=student.level)

    if query:
        courses_qs = courses_qs.filter(name__icontains=query)

    courses_qs = courses_qs.order_by('-created_at')
    paginator = Paginator(courses_qs, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    if student:
        enrollments = {e.course_id: e.status for e in Enrollment.objects.filter(student=student)}
        for course in page_obj:
            course.enrollment_status = enrollments.get(course.id, 'none')
            course.is_enrolled = (course.enrollment_status == 'approved')
            course.is_pending = (course.enrollment_status == 'pending')
            course.is_rejected = (course.enrollment_status == 'rejected')

    return render(request, 'student/courses.html', {
        'courses': page_obj,
        'page_obj': page_obj,
    })


@student_required
def student_course_enroll(request, course_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    student = getattr(request.user, 'student_profile', None)
    if not student:
        messages.error(request, "لم يتم العثور على ملف طالب لهذا الحساب.")
        return redirect('student_courses')

    course = get_object_or_404(Course, id=course_id)
    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        course=course,
        defaults={'status': Enrollment.Status.PENDING}
    )

    if not created:
        enrollment.status = Enrollment.Status.PENDING
        enrollment.requested_at = timezone.now()
        enrollment.decided_at = None
        enrollment.save()

    messages.info(request, f"تم إرسال طلب الانضمام لمقرر '{course.name}' بنجاح.")
    return redirect(request.META.get('HTTP_REFERER') or 'student_courses')


@student_required
def student_my_courses(request):
    student = getattr(request.user, 'student_profile', None)
    if student:
        approved_enrollments = Enrollment.objects.filter(
            student=student,
            status=Enrollment.Status.APPROVED
        ).select_related('course', 'course__doctor', 'course__specialization').order_by('-decided_at')
        enrolled_courses = [e.course for e in approved_enrollments]
    else:
        enrolled_courses = []

    paginator = Paginator(enrolled_courses, 6)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'student/my_courses.html', {
        'enrolled_courses': page_obj,
        'page_obj': page_obj,
    })


@student_required
def student_course_detail(request, course_id):
    student = getattr(request.user, 'student_profile', None)
    course = get_object_or_404(Course, id=course_id)

    if student and not request.user.is_superuser:
        is_approved = Enrollment.objects.filter(
            student=student,
            course=course,
            status=Enrollment.Status.APPROVED
        ).exists()
        if not is_approved:
            messages.warning(request, "يجب اعتماد تسجيلك في هذا المقرر أولاً لتتمكن من الوصول للمحاضرات.")
            return redirect('student_courses')

    lectures = course.lectures.all().order_by('number')
    return render(request, 'student/course_detail.html', {
        'course': course,
        'lectures': lectures,
    })


@student_required
def student_lecture_detail(request, course_id, lecture_id):
    student = getattr(request.user, 'student_profile', None)
    course = get_object_or_404(Course, id=course_id)

    if student and not request.user.is_superuser:
        is_approved = Enrollment.objects.filter(
            student=student,
            course=course,
            status=Enrollment.Status.APPROVED
        ).exists()
        if not is_approved:
            messages.warning(request, "لا تمتلك الصلاحية لمشاهدة محتوى هذه المحاضرة.")
            return redirect('student_courses')

    lecture = get_object_or_404(Lecture, id=lecture_id, course=course)
    return render(request, 'student/lecture_detail.html', {
        'course': course,
        'lecture': lecture,
    })


@student_required
def student_profile(request):
    return render(request, 'student/profile.html')


# ==============================================================================
# صفحات الخطأ (Error Handlers)
# ==============================================================================

def custom_403_view(request, exception=None):
    return render(request, '403.html', status=403)


def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)


def custom_500_view(request):
    return render(request, '500.html', status=500)
