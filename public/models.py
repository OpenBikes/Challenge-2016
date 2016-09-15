from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)


class Curriculum(models.Model):

    class Meta:
        db_table = 'curriculums'
        verbose_name_plural = 'Curriculums'

    name = models.CharField(verbose_name='Curriculum', max_length=50)
    school = models.CharField(verbose_name='School', max_length=50)

    def __str__(self):
        return '{}, {}'.format(self.name, self.school)


class Team(models.Model):

    class Meta:
        db_table = 'teams'
        verbose_name_plural = 'Teams'

    name = models.CharField(verbose_name='Name', max_length=50)
    creation = models.DateField(verbose_name='Date of creation')
    Curriculum = models.ForeignKey(Curriculum)

    def __str__(self):
        return '{}, {}, {}'.format(self.name, self.curriculum.name, self.curriculum.school)

    @property
    def captain(self):
        return self.person_set.filter(is_captain=True).first()


class Person(models.Model):

    class Meta:
        db_table = 'persons'
        verbose_name_plural = 'Persons'

    first_name = models.CharField(verbose_name='First name', max_length=50)
    last_name = models.CharField(verbose_name='Last name', max_length=100)
    date_of_birth = models.DateField(verbose_name='Date of birth')
    team = models.ForeignKey(Team, null=True)
    is_captain = models.BooleanField(default=False, verbose_name='Captain')

    USERNAME_FIELD = 'email'

    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def create_user(self, email, password):
        '''
        Create a user account to log in.
        '''
        user = User.objects.create(
            email=email,
            person_id=self.pk
        )
        user.set_password(password)
        user.save()

    def __str__(self):
        return self.full_name


class Submission(models.Model):

    class Meta:
        db_table = 'submissions'
        verbose_name_plural = 'Submissions'

    at = models.DateTimeField(verbose_name='At')
    by = models.ForeignKey(Person)
    team = models.ForeignKey(Team)
    valid = models.BooleanField(verbose_name='Valid')
    score = models.FloatField(verbose_name='Score')

    def __str__(self):
        return '{}, {}, {}'.format(self.by, self.by.team, self.at)


class Newsletter(models.Model):

    class Meta:
        db_table = 'newsletter'
        verbose_name_plural = 'Newsletters'

    USER_TYPES = (
        ('captain', 'Only team leaders'),
        ('student', 'All students'),
    )
    STATUS_CHOICES = (
        ('queue', 'In Queue'),
        ('sent', 'Sent'),
    )

    usertype = models.CharField(max_length=50, choices=USER_TYPES, verbose_name='User type')
    subject = models.CharField(max_length=100, verbose_name='Subject')
    message = models.TextField(blank=True, verbose_name='Message')
    sentdate = models.DateTimeField(auto_now=True, verbose_name='Sent date')
    status = models.CharField(max_length=30, default='queue', choices=STATUS_CHOICES, verbose_name='Email status')


class UserManager(BaseUserManager):

    def create_user(self, email, password=None):
        '''
        Creates and saves a User with the given email, date of birth and
        password.
        '''
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email)
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        '''
        Creates and saves a superuser with the given email, date of birth and
        password.
        '''
        user = self.create_user(
            email,
            password=password
        )

        user.is_active = True
        user.is_admin = True
        user.save()
        return user


class User(AbstractBaseUser):

    '''
    A `User` is a general user of the application which serves as a mixin for
    the different kind of users.
    '''

    class Meta:
        db_table = 'users'
        verbose_name_plural = 'Users'

    email = models.EmailField(
        verbose_name='Email address',
        max_length=200,
        unique=True
    )

    is_active = models.BooleanField(verbose_name='Active', default=False)
    is_admin = models.BooleanField(verbose_name='Admin', default=False)

    person = models.OneToOneField(Person, null=True, on_delete=models.CASCADE)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    @classmethod
    def has_perm(cls, perm, obj=None):
        '''
        Does the user have a specific permission? The simplest possible answer
        is "Yes, always."
        '''
        return True

    @classmethod
    def has_module_perms(cls, app_label):
        '''
        Does the user have permissions to view the app `app_label`? The
        simplest possible answer is "Yes, always."
        '''
        return True

    @property
    def is_staff(self):
        '''
        Is the user a member of staff? The simplest possible answer is "All
        admins are staff."
        '''
        return self.is_admin

    def __str__(self):
        return self.get_full_name()
