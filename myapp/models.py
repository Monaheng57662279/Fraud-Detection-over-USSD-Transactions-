import pickle
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class Transaction(models.Model):
    # Auto-generated numeric ID as primary key
    id = models.AutoField(primary_key=True)
    contact_num = models.CharField(max_length=20)
    merchant = models.CharField(max_length=255, default='uncategorized')
    category = models.CharField(max_length=255, default='uncategorized')
    amt = models.DecimalField(max_digits=10, decimal_places=2)
    unix_time = models.IntegerField()
    is_fraud = models.BooleanField()
    trans_datetime = models.DateTimeField()

    class Meta:
        db_table = 'csv_table'

class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, username, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    email = models.EmailField(max_length=254, unique=True)
    username = models.CharField(max_length=150, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    mobile_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    bio = models.TextField(blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']

    def __str__(self):
        return self.username

def load_fraud_detection_model():
    with open('train.pkl', 'rb') as f:
        return pickle.load(f)
    
def load_label_encoders():
    with open('labels.pkl', 'rb') as f:
        return pickle.load(f)


class UploadCSV(models.Model):
    contact_num = models.CharField(primary_key=True, max_length=20)
    merchant = models.CharField(max_length=255, default='uncategorized')
    category = models.CharField(max_length=255, default='uncategorized')
    amt = models.DecimalField(max_digits=10, decimal_places=2)
    unix_time = models.IntegerField()
    is_fraud = models.BooleanField()
    trans_datetime = models.DateTimeField()

    def __str__(self):
        return self.contact_num


class RealTime(models.Model):
    id = models.AutoField(primary_key=True)
    contact_num = models.CharField(max_length=20)
    merchant = models.CharField(max_length=255, default='uncategorized')
    category = models.CharField(max_length=255, default='uncategorized')
    amt = models.DecimalField(max_digits=10, decimal_places=2)
    unix_time = models.IntegerField()
    trans_datetime = models.DateTimeField()

    class Meta:
        db_table = 'real_table'


from django.db import models

# 1. 👇 Add the following line
class Notification(models.Model):
    message = models.CharField(max_length=100)
    
    def __str__(self):
        return self.message        