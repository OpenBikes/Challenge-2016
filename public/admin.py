from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.core.mail import EmailMessage
from django.shortcuts import render
from django.template.loader import render_to_string

from .models import (
    Person,
    User,
    School,
    Submission,
    Team,
    Newsletter
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


@admin.register(Newsletter)
class Newsletter(admin.ModelAdmin):
    list_display = (
        'usertype',
        'subject',
        'message',
        'sentdate',
        'status'
    )

    search_fields = list_display
    ordering = list_display
    actions = ['send_newsletter']

    def send_newsletter(self, request, queryset):
        # Loop through newletters in queue
        for newsletter in queryset:
            # Load all students
            students = User.objects.filter().all()
            # If newsletter is adressed to only team leaders, load them
            print(newsletter.subject, newsletter.usertype)
            if newsletter.status == 'queue' and newsletter.usertype == 'captain':
                recipient = {
                    student.person.full_name: student.get_full_name() for student in students if student.person and student.person.is_captain}
            # Else load all students
            elif newsletter.status == 'queue':
                recipient = {
                    student.person.full_name: student.get_full_name() for student in students if student.person}

            try:
                # Send emails to designated students
                for name, email in recipient.items():
                    self.send_email(request, name, email, newsletter.subject, newsletter.message)
                # Update newsletter status and output number of newsletters sent
                queryset.update(status='sent')
            except:
                self.message_user(
                    request, "Newsletter ({subject}) had already been sent, you can't publish it twice.".format(subject=newsletter.subject), level=messages.ERROR)
            else:
                nb_students = len(recipient.keys())
                students = '{} student'.format(nb_students) if nb_students == 1 else '{} students'.format(nb_students)
                msg_success = 'Newsletter ({subject}) was successfully sent to {students}'.format(
                    subject=newsletter.subject, students=students)
                self.message_user(request, msg_success)

    send_newsletter.short_description = 'Send selected newsletter to students'

    def send_email(self, request, name, email, subject, message):
        try:
            sender = '{admin}@gmail.com'.format(admin=settings.EMAIL_HOST_USER)
            recipient = email
            context = {
                'email': email,
                'student': name,
                'subject': subject,
                'message': message
            }
            message = render_to_string('public/email/newsletter.html', context)
            msg = EmailMessage(context.get('subject'), message, sender, [recipient])
            msg.content_subtype = 'html'
            msg.send()
            return render(request, 'public/email/newsletter.html', context)
        except Error as e:
            print('Error sending message:', e)
            return
