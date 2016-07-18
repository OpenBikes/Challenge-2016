from django.contrib import admin
from django.contrib.auth.models import Group

from .models import (
    Person,
    User,
    School,
    Submission,
    Team
)


admin.site.unregister(Group)


class UserInline(admin.StackedInline):
    model = User


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):

    inlines = (UserInline,)
    list_display = (
        'first_name',
        'last_name',
        'date_of_birth'
    )
    search_fields = list_display
    ordering = list_display


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    pass


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    pass


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    pass
