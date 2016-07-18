from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser
)


class School(models.Model):

    class Meta:
        db_table = 'schools'
        verbose_name_plural = 'Schools'

    name = models.CharField(verbose_name='School', max_length=50)
    city = models.CharField(verbose_name='City', max_length=50)

    def __str__(self):
        return '{}, {}'.format(self.name, self.city)


class Team(models.Model):

    class Meta:
        db_table = 'teams'
        verbose_name_plural = 'Teams'

    name = models.CharField(verbose_name='Name', max_length=50)
    creation = models.DateField(verbose_name='Date of creation')
    school = models.ForeignKey(School)

    def __str__(self):
        return '{}, {}, {}'.format(self.name, self.school.name, self.school.city)

    @property
    def members(self):
        return self.person_set.filter(team=self).all()

    @property
    def captain(self):
        return self.person_set.filter(captain=True).first()


class Person(models.Model):

    class Meta:
        db_table = 'persons'
        verbose_name_plural = 'Persons'

    first_name = models.CharField(verbose_name='First name', max_length=50)
    last_name = models.CharField(verbose_name='Last name', max_length=100)
    date_of_birth = models.DateField(verbose_name='Date of birth')
    team = models.ForeignKey(Team, null=True)
    captain = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    @property
    def postal_address(self):
        '''
        The `postal_address` contains information ordered by importance, from
        minor to major.
        '''
        return '{}, {}'.format(
            self.full_name,
            self.location.address
        )

    @property
    def full_name(self):
        '''
        The `full_name` is the concatenation of the `first_name` and the
        `last_name`.
        '''
        return '{} {}'.format(self.first_name, self.last_name)

    def __str__(self):
        return self.full_name

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


class Submission(models.Model):

    class Meta:
        db_table = 'submissions'
        verbose_name_plural = 'Submissions'

    at = models.DateTimeField(verbose_name='At')
    by = models.ForeignKey(Person)
    valid = models.BooleanField(verbose_name='Valid')
    score = models.FloatField(verbose_name='Score')

    def __str__(self):
        return '{}, {}, {}'.format(self.by, self.by.team, self.at)


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
