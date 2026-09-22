from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from .models import Specialization, Level, StudentProfile, DoctorProfile, Course, Lecture


class LoginForm(forms.Form):
    username = forms.CharField(
        label="اسم المستخدم أو الرقم الأكاديمي / الوظيفي",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المستخدم أو الرقم الجامعي / الوظيفي',
            'autocomplete': 'username',
        })
    )
    password = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        identifier = (cleaned_data.get('username') or '').strip()
        password = cleaned_data.get('password')

        if identifier and password:
            # 1. Look up user by username
            user_obj = User.objects.filter(username__iexact=identifier).first()

            # 2. Look up by student university_id
            if not user_obj:
                student = StudentProfile.objects.filter(university_id__iexact=identifier).select_related('user').first()
                if student:
                    user_obj = student.user

            # 3. Look up by doctor employee_id
            if not user_obj:
                doctor = DoctorProfile.objects.filter(employee_id__iexact=identifier).select_related('user').first()
                if doctor:
                    user_obj = doctor.user

            if user_obj:
                if not user_obj.is_active:
                    raise forms.ValidationError(
                        "هذا الحساب معطل حالياً بانتظار موافقة الإدارة الأكاديمية (مدير النظام)."
                    )
                user = authenticate(username=user_obj.username, password=password)
                if not user:
                    raise forms.ValidationError(
                        "كلمة المرور غير صحيحة. يرجى التحقق وإعادة المحاولة."
                    )
                self.user_cache = user
            else:
                raise forms.ValidationError(
                    "بيانات الدخول غير صحيحة. يرجى التأكد من اسم المستخدم / الرقم الأكاديمي وكلمة المرور."
                )

        return cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


class RegistrationForm(forms.Form):
    USER_TYPE_CHOICES = [
        ('student', 'طالب'),
        ('doctor', 'دكتور'),
    ]

    user_type = forms.ChoiceField(
        choices=USER_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'role-option-radio'}),
        initial='student'
    )
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثال: أحمد محمد ',
        })
    )
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مثال: 44102938',
            'autocomplete': 'username',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@university.edu',
            'autocomplete': 'email',
        })
    )
    specialization = forms.ModelChoiceField(
        queryset=Specialization.objects.all(),
        empty_label="اختر التخصص...",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_specialization'})
    )
    level = forms.ModelChoiceField(
        queryset=Level.objects.all(),
        required=False,
        empty_label="اختر المستوى الدراسي...",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_level'})
    )
    password = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        })
    )
    password_confirm = forms.CharField(
        min_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••••',
            'autocomplete': 'new-password',
        })
    )

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("اسم المستخدم / الرقم الأكاديمي مسجل مسبقاً في النظام.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("البريد الإلكتروني مسجل مسبقاً في النظام.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        user_type = cleaned_data.get("user_type")
        level = cleaned_data.get("level")
        specialization = cleaned_data.get("specialization")

        if password and password_confirm and password != password_confirm:
            self.add_error("password_confirm", "كلمتا المرور غير متطابقتين.")

        if user_type == 'student':
            if specialization and Level.objects.filter(specialization=specialization).exists() and not level:
                self.add_error("level", "يرجى تحديد المستوى الدراسي للطالب.")

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        full_name = cleaned_data['full_name'].strip()
        parts = full_name.split(maxsplit=1)
        first_name = parts[0] if parts else ''
        last_name = parts[1] if len(parts) > 1 else ''

        user_type = cleaned_data['user_type']
        is_active = (user_type != 'doctor')

        user = User.objects.create_user(
            username=cleaned_data['username'],
            email=cleaned_data['email'],
            password=cleaned_data['password'],
            first_name=first_name,
            last_name=last_name,
            is_active=is_active
        )

        if user_type == 'student':
            StudentProfile.objects.create(
                user=user,
                university_id=cleaned_data['username'],
                specialization=cleaned_data['specialization'],
                level=cleaned_data.get('level')
            )
        else:
            doctor_profile = DoctorProfile.objects.create(
                user=user,
                employee_id=cleaned_data['username']
            )
            if cleaned_data.get('specialization'):
                doctor_profile.specializations.add(cleaned_data['specialization'])

        return user


class LectureForm(forms.ModelForm):
    order = forms.IntegerField(
        min_value=1,
        label="رقم المحاضرة",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'id': 'id_order',
            'min': '1',
            'placeholder': '1',
        })
    )

    class Meta:
        model = Lecture
        fields = ['title', 'description', 'points', 'file', 'video']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_title',
                'placeholder': 'مثال: مقدمة في  .......',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'id_description',
                'rows': 3,
                'placeholder': 'نبذة توضح أهداف وموضوعات المحاضرة...',
            }),
            'points': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'id_points',
                'rows': 4,
                'placeholder': 'اكتب النقاط الرئيسية (كل نقطة في سطر مستقل)...',
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'id_file',
                'accept': '.pdf,.doc,.docx,.ppt,.pptx',
            }),
            'video': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'id_video',
                'accept': 'video/mp4,video/webm',
            }),
        }

    def __init__(self, *args, course=None, **kwargs):
        self.course = course
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['order'].initial = self.instance.number
            self.initial['order'] = self.instance.number
            if not self.course:
                self.course = self.instance.course
        elif self.course:
            # Suggest next lecture number automatically
            last_lec = self.course.lectures.order_by('-number').first()
            next_num = (last_lec.number + 1) if last_lec else 1
            self.fields['order'].initial = next_num
            self.initial['order'] = next_num

    def clean_order(self):
        order = self.cleaned_data['order']
        if self.course:
            qs = Lecture.objects.filter(course=self.course, number=order)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f"المحاضرة رقم {order} موجودة بالفعل في هذا المقرر. يرجى اختيار رقم آخر.")
        return order

    def save(self, commit=True):
        lecture = super().save(commit=False)
        lecture.number = self.cleaned_data['order']
        if self.course:
            lecture.course = self.course
        if commit:
            lecture.save()
        return lecture
