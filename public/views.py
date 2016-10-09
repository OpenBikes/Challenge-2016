import datetime as dt

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import connection
from django.http import Http404
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from itsdangerous import URLSafeTimedSerializer

from public.models import Person, User, Curriculum, Submission, Team


# Random token generator
TS = URLSafeTimedSerializer(settings.SECRET_KEY)


def index(request):
    cursor = connection.cursor()
    cursor.execute('''
    SELECT
        teams.name as name,
        curriculums.school as curriculum,
        MAX(submissions.score) as best_score,
        COUNT(submissions.id) as nbr_submissions,
        strftime('%Y/%m/%d', MIN(submissions.at)) as last_submission
    FROM
        persons,
        submissions,
        teams,
        curriculums
    WHERE
        persons.team_id = teams.id AND
        submissions.by_id = persons.id AND
        curriculums.id = teams.curriculum_id AND
        submissions.at < datetime('now', '-1 hour')
    GROUP BY
        teams.id;
    ''')
    context = {
        'cursor': cursor,
    }
    return render(request, 'public/index.html', context)


def faq(request):
    return render(request, 'public/faq.html')


def register(request):
    if request.method == 'POST':
        form = request.POST
        user = User.objects.filter(email=form['email']).first()
        # Check if the user already exists
        if user:
            messages.error(
                request, 'Cette adresse email est déjà associée à un compte.')
            return render(request, 'public/auth/registration.html')
        person = Person(
            first_name=form['first_name'],
            last_name=form['last_name'],
            date_of_birth=dt.datetime.strptime(
                form['date_of_birth'], '%d/%m/%Y')
        )
        person.save()
        user = person.create_user(
            email=form['email'], password=form['password1'])
        # Send a confirmation email
        token = TS.dumps(form['email'], salt='email-confirm-key')
        context = {
            'link': request.build_absolute_uri(reverse('public:confirm_registration',
                                                       kwargs={'token': token})),
        }
        subject = 'Confirmation de compte'
        sender = 'noreply.aidor@gmail.com'
        recipient = form['email']
        message = render_to_string(
            'public/email/auth/registration_confirmation.html', context)
        msg = EmailMessage(subject, message, sender, [recipient])
        msg.content_subtype = 'html'
        try:
            msg.send()
            print('Email sent')
        except Exception as exc:
            person.delete()
            raise exc
        # Notify the user
        context = {
            'email': form['email'],
        }
        return render(request, 'public/auth/registration_completion.html', context)
    return render(request, 'public/auth/registration.html')


def confirm_registration(request, token):
    try:
        email = TS.loads(token, salt='email-confirm-key', max_age=86400)
    except:
        raise Http404
    # Activate the user's account
    user = User.objects.filter(email=email).first()
    user.is_active = True
    user.save()
    # Notify the user and send him to the login page
    messages.success(
        request, 'Votre compte a bien été activé! Vous pouvez à présent vous connecter.')
    return redirect('public:login')


def login_user(request):
    if request.method == 'POST':
        form = request.POST
        email = form['email']
        password = form['password']
        user = authenticate(email=email, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('public:account')
            else:
                messages.error(
                    request, "L'adresse email de ce compte n'a pas été confirmée.")
                return render(request, 'public/auth/login.html')
        else:
            messages.error(
                request, "Les identifiants que vous nous avez fournis sont invalides.")
            return render(request, 'public/auth/login.html')
    return render(request, 'public/auth/login.html')


def logout_user(request):
    logout(request)
    return redirect('public:index')


def password_forgotten(request):
    if request.method == 'POST':
        form = request.POST
        user = User.objects.filter(email=form['email']).first()
        # Check if the user exists
        if not user:
            messages.error(
                request, "Aucun compte n'est associée à cette adresse email.")
            return render(request, 'public/auth/password_forgotten.html')
        # Send a reset email
        token = TS.dumps(form['email'], salt='email-reset-key')
        context = {
            'link': request.build_absolute_uri(reverse('public:password_reset',
                                                       kwargs={'token': token})),
        }
        subject = 'Réinitialisation de mot de passe'
        sender = 'noreply.aidor@gmail.com'
        recipient = form['email']
        message = render_to_string(
            'public/email/auth/password_forgotten_confirmation.html', context)
        msg = EmailMessage(subject, message, sender, [recipient])
        msg.content_subtype = 'html'
        msg.send()
        # Notify the user
        context = {
            'email': form['email'],
        }
        return render(request, 'public/auth/password_forgotten_completion.html', context)
    return render(request, 'public/auth/password_forgotten.html')


def password_reset(request, token):
    if request.method == 'POST':
        form = request.POST
        try:
            email = TS.loads(token, salt='email-reset-key', max_age=86400)
        except:
            raise Http404
        # Activate the user's account
        user = User.objects.filter(email=email).first()
        if user:
            # Check the account has been confirmed
            if user.is_active is False:
                messages.error(
                    request, "L'adresse email de ce compte n'a pas été confirmée.")
                return render(request, 'public/auth/password_forgotten.html')
            user.set_password(form['password1'])
            user.save()
            # Notify the user and send him to the login page
            messages.success(
                request, 'Votre mot de passe a bien été changé. Vous pouvez à présent vous connecter.')
            return redirect('public:login')
        else:
            messages.error(
                request, "Aucun compte n'est associée à cette adresse email.")
            return render(request, 'public/auth/password_forgotten.html')
    context = {
        'token': token,
    }
    return render(request, 'public/auth/password_reset.html', context)


@login_required(login_url='/login')
def account(request):

    person = request.user.person
    team = person.team
    time_threshold = dt.datetime.now()-dt.timedelta(hours=1)

    # The person has a team
    if team:
        context = {
            'team_members': [
                {
                    'id': member.id,
                    'full_name': member.full_name,
                    'is_captain': member.is_captain,
                    'submissions': member.submission_set.filter(team=person.team)
                                                        .filter(at__lt=time_threshold)
                                                        .order_by('at').all()
                }
                for member in team.person_set.all()
            ],
            'teams': Team.objects.order_by('name').all()
        }
    # The user doesn't yet have a team
    else:
        context = {
            'curriculums': Curriculum.objects.order_by('name').all(),
            'teams': Team.objects.order_by('name').all()
        }

    return render(request, 'public/account.html', context)


@login_required(login_url='/login')
def join_team(request):
    form = request.POST
    team = Team.objects.filter(id=form['team_id']).first()
    captain = team.captain
    person = request.user.person
    if person.team == captain.team:
        messages.success(request, 'Vous êtes déjà membre de cette équipe.')
        return redirect('public:account')
    # Send a reset email
    token = TS.dumps(captain.user.email, salt='email-join-key')
    context = {
        'link': request.build_absolute_uri(reverse('public:accept_member',
                                                   kwargs={
                                                       'token': token,
                                                       'person_id': person.id
                                                   })),
        'team': team,
        'captain': captain,
        'person': person
    }
    subject = 'Demande pour rejoindre votre équipe'
    sender = 'noreply.aidor@gmail.com'
    recipient = captain.user.email
    message = render_to_string('public/email/accept_member.html', context)
    msg = EmailMessage(subject, message, sender, [recipient])
    msg.content_subtype = 'html'
    msg.send()
    # Redirect and notify the user that the email has been sent
    messages.success(
        request, "Votre demande a été envoyée par email au capitaine de l'équipe.")
    return redirect('public:index')


@login_required(login_url='/login')
def accept_member(request, token, person_id):
    form = request.POST
    try:
        email = TS.loads(token, salt='email-join-key', max_age=86400)
    except:
        raise Http404

    person = Person.objects.filter(id=person_id).first()
    person.team = request.user.person.team
    person.save()

    messages.success(
        request, '{} a rejoint votre équipe.'.format(person.full_name))
    return redirect('public:account')


@login_required(login_url='/login')
def create_team(request):
    form = request.POST
    curriculum = Curriculum.objects.filter(id=form['curriculum_id']).first()
    team = Team(name=form['name'], curriculum=curriculum,
                creation=timezone.now())
    team.save()
    request.user.person.team = team
    request.user.person.is_captain = True
    request.user.person.save()
    return redirect('public:account')


@login_required(login_url='/login/')
def make_submission(request):
    file = request.FILES['file']
    guess = [
        row.split(',')
        for row in file.read().decode('utf-8').splitlines()
    ][1:]
    truth = [
        row.split(',')
        for row in open('test-filled.csv').read().splitlines()
    ][1:]
    total_error = 0
    for g, t in zip(guess, truth):
        if (g[:3] != t[:3]) or g[3] == '':
            messages.error(request, 'Le fichier que vous avez soumis est invalide.')
            return render(request, 'public/account.html')
        total_error += abs(float(g[3]) - float(t[3]))
    mean_error = total_error / len(guess)
    submission = Submission(
        at=dt.datetime.now(),
        by=request.user.person,
        team=request.user.person.team,
        valid=True,
        score=mean_error
    )
    submission.save()
    messages.success(request, 'Votre soumission a été corrigée. Vous connaîtrez son score dans une heure.')
    return redirect('public:account')


@login_required(login_url='/login/')
def remove_team_member(request, person_id):
    person = Person.objects.filter(id=person_id).first()
    person.team = None
    person.save()

    messages.success(
        request, '{} a été retiré de votre équipe.'.format(person.full_name))
    return redirect('public:account')


@login_required(login_url='/login/')
def name_captain(request, person_id):

    # Destitute the current captain
    request.user.person.is_captain = False
    request.user.person.save()

    # Promote the chosen member
    person = Person.objects.filter(id=person_id).first()
    person.is_captain = True
    person.save()

    messages.success(
        request, '{} est maintenant le capitaine de votre équipe.'.format(person.full_name))
    return redirect('public:account')
