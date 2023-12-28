from django.db import models
from django.contrib.auth.models import AbstractUser, AbstractBaseUser, PermissionsMixin, BaseUserManager, UserManager
from django.contrib.auth.models import Group, Permission


class NewUserManager(BaseUserManager):

    def create_user(self,email,password=None, **extra_fields):
        if not email:
            raise ValueError('Поле "email" обязательно')
        
        email = self.normalize_email(email) 
        user = self.model(email=email, **extra_fields) 
        user.set_password(password)
        user.save(using=self.db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)
    


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(("email адрес"), unique=True)
    username = models.CharField(max_length=30, default='', verbose_name="Имя пользователя")
    password = models.TextField(max_length=256, verbose_name="Пароль")    
    is_staff = models.BooleanField(default=False, verbose_name="Является ли пользователь менеджером?")
    is_superuser = models.BooleanField(default=False, verbose_name="Является ли пользователь админом?")

    is_active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group, verbose_name=("groups"), blank=True, related_name="custom_user_groups")
    user_permissions = models.ManyToManyField(Permission, blank=True, related_name="custom_user_permissions")

    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    objects =  NewUserManager()
    class Meta:
        managed = True
    





class Sphere(models.Model):
    id = models.AutoField(primary_key=True)
    sphere_name = models.CharField(max_length=100)


    def __str__(self):
        return self.sphere_name

    class Meta:
        managed = True
        verbose_name_plural = 'Сфера применения'



class Disease(models.Model):
    id = models.AutoField(primary_key=True)
    disease_name = models.CharField(default='Название болезни', max_length=150)
    general_info = models.CharField(default='Общая информация о болезни', max_length=255)
    simptoms = models.CharField(default='Симптомы', max_length=255)
    sphere_id = models.ForeignKey(Sphere, on_delete=models.CASCADE)
    image = models.TextField(default='')

    STATUSES = [
        ('a', 'active'),
        ('d', 'delited')
    ]
    status = models.CharField(max_length=1, choices=STATUSES)


    def __str__(self):
        print("return self.name")
        return self.disease_name

    def sphere_name(self):
        return self.sphere_id.sphere_name
    
    def image64(self):
        print("1")
        a= str(self.image.tobytes())[2:]
        a = a[:-1]
        return a
    
    


    class Meta:
        managed = True
        verbose_name_plural = 'Заболевания'



class User(models.Model):
    id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.user_name

    class Meta:
        managed = True
        verbose_name_plural = 'Пользователи'


class Medical_drug(models.Model):
    id =models.AutoField(primary_key=True)
    drug_name = models.CharField(max_length=150, default='Название лекарства')
    sphere_id = models.ForeignKey(Sphere, on_delete=models.CASCADE, default=1)
    # автоматом ставим время только при изменении объекта, а не при создании
    time_create = models.DateField(blank=True, null=True) 
    time_form = models.DateField(blank=True, null=True) 
    time_finish = models.DateField(blank=True, null=True)
    price = models.IntegerField(default=0)
    for_disease = models.ManyToManyField(Disease, through='DiseaseDrug', null=False)
    STATUSES = [
        (0, 'Черновик'), # Черновик - 'entered'
        (1, 'Сформирована'), # на рассмотрениии - 'in operation'  - юзер смена
        (2, 'Завершён'), # завершён - 'finished' - (одобрен) админ
        (3, 'Отменён'), # отменён - 'cancelled'  - (отклонен) админ
        (4, 'Удалён') # удалён - 'deleted'  - юзер смена
    ]
    TEST_STATUSES = [
        (0, 'Не удалось обратиться к асинхронному сервису'),
        (1, 'Успех'),
        (2, 'Неуспех'),
    ]
    status = models.IntegerField(choices=STATUSES, default=0)
    test_status = models.IntegerField(choices=TEST_STATUSES, default=1)
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, default=1)
    moderator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='moderator', blank=True, null=True)
    


    def __str__(self):
        return self.drug_name
    
    def disease_name(self):
        return self.for_disease.all()
    
    def get_test_status_display_word(self):
        status_test = dict(self.TEST_STATUSES)
        return status_test.get(self.test_status, 'Unknown')
    
    def get_grug_display_word(self):
        status_drug = dict(self.STATUSES)
        return status_drug.get(self.status, 'Unknown')
    
    class Meta:
        managed = True
        verbose_name_plural = 'Медицинские препараты'
    


class DiseaseDrug(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE)
    drug = models.ForeignKey(Medical_drug, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.disease}   -   {self.drug}"

    class Meta:
        managed = True
        verbose_name_plural = 'Заболевания-препараты'


# class Session(models.Model):
#     session_key = models.CharField(primary_key=True, max_length=40)
#     session_data = models.TextField()
#     expire_date = models.DateTimeField()

#     class Meta:
#         managed = False
#         db_table = 'django_session'



   
