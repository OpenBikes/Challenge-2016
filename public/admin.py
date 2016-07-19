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


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):

    class UserInline(admin.StackedInline):
        model = User

    inlines = (UserInline,)

    list_display = (
        'first_name',
        'last_name',
        'date_of_birth',
        'is_captain'
    )

    search_fields = list_display
    ordering = list_display


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'city'
    )

    search_fields = list_display
    ordering = list_display


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):

    list_display = (
        'at',
        'by',
        'score',
        'valid'
    )

    search_fields = list_display
    ordering = list_display


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'school'
    )

    search_fields = list_display
    ordering = list_display
