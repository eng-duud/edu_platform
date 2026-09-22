from django.db import models
from django.contrib.auth.models import User


class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Level(models.Model):
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name="levels")
    name = models.CharField(max_length=100)
    number = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ["specialization", "number"]
        unique_together = ["specialization", "number"]

    def __str__(self):
        return f"{self.specialization.name} - {self.name}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    university_id = models.CharField(max_length=50, unique=True)
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT, related_name="students")
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True, related_name="students")


    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def student_id(self):
        return self.university_id

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    employee_id = models.CharField(max_length=50, unique=True)
    specializations = models.ManyToManyField(Specialization, related_name="doctors", blank=True)


    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def specialization(self):
        return self.specializations.first()

    def get_specializations_display(self):
        specs = self.specializations.all()
        if specs.exists():
            return "، ".join(s.name for s in specs)
        return "غير محدد"



class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.PROTECT, related_name="courses")
    specialization = models.ForeignKey(Specialization, on_delete=models.PROTECT, related_name="courses")
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, null=True, blank=True, related_name="courses")
    course_file = models.FileField(upload_to="courses/")
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.name

    @property
    def file(self):
        return self.course_file

    @property
    def syllabus(self):
        return self.course_file

    @property
    def students_count(self):
        return self.enrollments.filter(status="approved").count()

    @property
    def lectures_count(self):
        return self.lectures.count()


class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lectures")
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to="lectures/files/", blank=True, null=True)
    video = models.FileField(upload_to="lectures/videos/", blank=True, null=True)
    points = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ["number"]
        unique_together = ["course", "number"]


    def __str__(self):
        return f"{self.course.name} - Lecture {self.number}"

    @property
    def order(self):
        return self.number

    @order.setter
    def order(self, val):
        self.number = val

    @property
    def video_file(self):
        return self.video

    @property
    def key_points(self):
        return self.points

    @property
    def attachment(self):
        return self.file


class Enrollment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "قيد الانتظار"
        APPROVED = "approved", "مقبول"
        REJECTED = "rejected", "مرفوض"

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    requested_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["student", "course"], name="unique_student_course")
        ]

    def __str__(self):
        return f"{self.student} → {self.course}"

    @property
    def created_at(self):
        return self.requested_at

    @property
    def date(self):
        return self.requested_at
