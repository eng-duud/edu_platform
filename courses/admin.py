from django.contrib import admin

from .models import (
    Specialization,
    Level,
    StudentProfile,
    DoctorProfile,
    Course,
    Lecture,
    Enrollment,
)


class LevelInline(admin.TabularInline):
    model = Level
    extra = 1
    fields = ("name", "number")


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ("name", "levels_count")
    search_fields = ("name",)
    inlines = [LevelInline]

    def levels_count(self, obj):
        return obj.levels.count()
    levels_count.short_description = "عدد المستويات"


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("name", "specialization", "number")
    list_filter = ("specialization",)
    search_fields = ("name", "specialization__name")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user__first_name",
        "university_id",
        "specialization",
        "level",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "university_id",
    )
    list_filter = (
        "specialization",
        "level",
    )


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "user__first_name",
        "employee_id",
        "get_specializations",
        "courses_count",
        "is_active",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "employee_id",
    )
    list_filter = (
        "specializations",
        "user__is_active",
    )
    filter_horizontal = ("specializations",)
    actions = ["activate_doctors", "deactivate_doctors"]

    def get_specializations(self, obj):
        return obj.get_specializations_display()
    get_specializations.short_description = "التخصصات"

    def courses_count(self, obj):
        return obj.courses.count()
    courses_count.short_description = "المقررات المسندة"

    @admin.display(boolean=True, description="الحساب مفعل")
    def is_active(self, obj):
        return obj.user.is_active

    @admin.action(description="تفعيل حسابات أعضاء هيئة التدريس المحددة")
    def activate_doctors(self, request, queryset):
        count = 0
        for doctor in queryset:
            if not doctor.user.is_active:
                doctor.user.is_active = True
                doctor.user.save()
                count += 1
        self.message_user(request, f"تم تفعيل {count} حساب(ات) دكتور بنجاح.")

    @admin.action(description="تعطيل حسابات أعضاء هيئة التدريس المحددة")
    def deactivate_doctors(self, request, queryset):
        count = 0
        for doctor in queryset:
            if doctor.user.is_active:
                doctor.user.is_active = False
                doctor.user.save()
                count += 1
        self.message_user(request, f"تم تعطيل {count} حساب(ات) دكتور بنجاح.")



@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "doctor",
        "specialization",
        "level",
        "created_at",
    )
    search_fields = (
        "name",
        "doctor__user__first_name",
        "doctor__user__last_name",
    )
    list_filter = (
        "specialization",
        "level",
    )


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = (
        "course",
        "number",
        "title",
        "created_at",
    )
    search_fields = (
        "title",
        "course__name",
    )
    list_filter = (
        "course",
    )


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "course",
        "status",
        "requested_at",
        "decided_at",
    )
    search_fields = (
        "student__user__first_name",
        "student__user__last_name",
        "student__university_id",
        "course__name",
    )
    list_filter = (
        "status",
        "course",
    )