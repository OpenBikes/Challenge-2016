import datetime as dt

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Count, Max, Min
from django.http import Http404
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from itsdangerous import URLSafeTimedSerializer

from public.models import Person, User, School, Submission, Team


# Random token generator
TS = URLSafeTimedSerializer(settings.SECRET_KEY)


def index(request):
    teams = Team.objects.annotate(best_score=Max('person__submission__score'),
                                  nbr_submissions=Count('person__submission'),
                                  last_submission=Min('person__submission__at'))\
                        .order_by('best_score')
    context = {
        'teams': teams,
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
            messages.error(request, 'Cette adresse email est déjà associée à un compte.')
            return render(request, 'public/auth/registration.html')
        person = Person(
            first_name=form['first_name'],
            last_name=form['last_name'],
            date_of_birth=dt.datetime.strptime(form['date_of_birth'], '%d/%m/%Y')
        )
        person.save()
        user = person.create_user(email=form['email'], password=form['password1'])
        # Send a confirmation email
        token = TS.dumps(form['email'], salt='email-confirm-key')
        context = {
            'link': request.build_absolute_uri(reverse('public:confirm_registration',
                                                       kwargs={'token': token})),
        }
        subject = 'Confirmation de compte'
        sender = 'noreply.aidor@gmail.com'
        recipient = form['email']
        message = render_to_string('public/email/auth/registration_confirmation.html', context)
        msg = EmailMessage(subject, message, sender, [recipient])
        msg.content_subtype = 'html'
        msg.send()
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
    messages.success(request, 'Votre compte a bien été activé! Vous pouvez à présent vous connecter.')
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
                messages.error(request, "L'adresse email de ce compte n'a pas été confirmée.")
                return render(request, 'public/auth/login.html')
        else:
            messages.error(request, "Les identifiants que vous nous avez fournis sont invalides.")
            return render(request, 'public/auth/login.html')
    return render(request, 'public/auth/login.html')


def logout_user(request):
    logout(request)
    return render(request, 'public/index.html')


def password_forgotten(request):
    if request.method == 'POST':
        form = request.POST
        user = User.objects.filter(email=form['email']).first()
        # Check if the user exists
        if not user:
            messages.error(request, "Aucun compte n'est associée à cette adresse email.")
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
        message = render_to_string('public/email/auth/password_forgotten_confirmation.html', context)
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
                messages.error(request, "L'adresse email de ce compte n'a pas été confirmée.")
                return render(request, 'public/auth/password_forgotten.html')
            user.set_password(form['password1'])
            user.save()
            # Notify the user and send him to the login page
            messages.success(request, 'Votre mot de passe a bien été changé. Vous pouvez à présent vous connecter.')
            return redirect('public:login')
        else:
            messages.error(request, "Aucun compte n'est associée à cette adresse email.")
            return render(request, 'public/auth/password_forgotten.html')
    context = {
        'token': token,
    }
    return render(request, 'public/auth/password_reset.html', context)


@login_required(login_url='/login/')
def account(request):
    context = {
        'schools': School.objects.order_by('name').all(),
        'submissions': Submission.objects.filter(by=request.user.person)\
                                         .order_by('at')\
                                         .all(),
        'team_members': request.user.person.team.members
    }
    return render(request, 'public/account.html', context)


@login_required(login_url='/login/')
def create_team(request):
    form = request.POST
    school = School.objects.filter(id=form['school_id']).first()
    team = Team(name=form['name'], school=school, creation=dt.datetime.now())
    team.save()
    request.user.person.team = team
    request.user.person.captain = True
    request.user.person.save()
    return redirect('public:account')


@login_required(login_url='/login/')
def make_submission(request):
    file = request.FILES['file']
    rows = file.read().decode('utf-8').splitlines()
    data = [row.split(',') for row in rows]
    submission = Submission(
        at=dt.datetime.now(),
        by=request.user.person,
        valid=True,
        score=1
    )
    submission.save()
    return redirect('public:account')
