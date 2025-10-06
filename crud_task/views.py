from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Project, Task
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone

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

        # verification de la longueur
        if (len(user_id) > 100 or len(user_email) > 200 or len(password) > 200 or len(confirm) > 200):
            return render(request, 'crud_task/register.html', {
                'error': "Erreur! Veuillez reéssayer"
            })
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
    project = Project.objects.filter(p_user=user_id)
    tasks = Task.objects.filter(task_project__p_user=user)
    active_task = tasks.filter(task_status=True).count()
    finish_task = tasks.filter(task_finish=True).count()
    overdue_tasks_count = len([
        task for task in tasks
        if not task.task_finish  # Si elle n'est pas marquée comme terminée
        and task.task_duration is not None # Si une durée est définie
        and (task.task_creation + task.task_duration) < timezone.now() # Si l'échéance est passée
    ])
    return render(request, 'crud_task/compte.html', {
        'user': user,
        'project': project,
        'tasks': tasks,
        'active_task': active_task,
        'finish_task': finish_task,
        'overdue_task': overdue_tasks_count
    })


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
