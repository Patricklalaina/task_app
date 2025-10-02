from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import User
from django.contrib.auth.hashers import make_password, check_password

def index(request):
    if (request.session.get('user_id')):
        return redirect('compte')
    return render(request, 'crud_task/index.html')


def register(request):
    return render(request, 'crud_task/register.html')

def add_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_email = request.POST.get('user_email')
        password = request.POST.get('user_password')
        confirm = request.POST.get('user_password_confirm')

        # Vérification mot de passe
        if password != confirm:
            return render(request, 'crud_task/register.html', {
                'error': "Les mots de passe ne correspondent pas.",
                'user_id': user_id,
                'user_email': user_email
            })

        # Vérification identifiant déjà utilisé
        if User.objects.filter(user_id=user_id).exists():
            return render(request, 'crud_task/register.html', {
                'error': "Cet identifiant est déjà utilisé.",
                'user_email': user_email
            })

        # Si tout est bon → créer utilisateur
        User.objects.create(
            user_id=user_id,
            user_mail=user_email,
            user_pd=make_password(password),
            user_log=False
        )
        return redirect('home')

    return redirect('register')

def compte(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')  # Si pas connecté → login obligatoire

    user = User.objects.get(user_id=user_id)
    return render(request, 'crud_task/compte.html', {'user': user})


def login_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('user_password')

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            return render(request, 'crud_task/login.html', {
                'error': "Identifiant invalide."
            })

        # Vérification mot de passe
        if not check_password(password, user.user_pd):
            return render(request, 'crud_task/login.html', {
                'error': "Mot de passe incorrect.",
                'user_id': user_id
            })

        # Authentification réussie → stocker l'utilisateur dans la session
        request.session['user_id'] = user.user_id
        user.user_log = True
        user.save()

        return redirect('compte')  # Vue du compte

    return render(request, 'crud_task/login.html')

def logout_view(request):
    user_id = request.session.get('user_id')
    if user_id:
        user = User.objects.get(user_id=user_id)
        user.user_log = False
        user.save()

    request.session.flush()  # Vide toute la session
    return redirect('login')
