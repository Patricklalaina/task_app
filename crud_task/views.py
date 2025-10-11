from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Project, Task
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone
from django.utils.dateparse import parse_duration


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

# --- fonction utilitaire réutilisable ---
def render_compte_page(request, extra_context=None):
    """
    Récupère toutes les données du tableau de bord et rend compte.html.
    extra_context permet d'ajouter des variables comme 'error' ou 'success'.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    user = User.objects.get(user_id=user_id)
    projects = Project.objects.filter(p_user=user_id)
    tasks = Task.objects.filter(task_project__p_user=user)

    active_task = tasks.filter(task_status=True).count()
    finish_task = tasks.filter(task_finish=True).count()

    overdue_task = len([
        task for task in tasks
        if not task.task_finish
        and task.task_duration is not None
        and (task.task_creation + task.task_duration) < timezone.now()
    ])
    for projet in projects:
        projet.tasks = [task for task in tasks if task.task_project == projet]
    context = {
        'user': user,
        'project': projects,
        'active_task': active_task,
        'finish_task': finish_task,
        'overdue_task': overdue_task,
        "now": timezone.now(),
    }

    # on fusionne avec le contexte additionnel (error, success…)
    if extra_context:
        context.update(extra_context)

    return render(request, 'crud_task/compte.html', context)


def compte(request):
    return render_compte_page(request)


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


def get_user_in_request(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return None

def add_project(request):
    if request.method == 'POST':
        user = get_user_in_request(request)
        if not user:
            return redirect('login')

        name = request.POST.get('p_name')
        desc = (request.POST.get('p_desc') or '').strip()

        if len(name) > 100:
            # Appel de la fonction réutilisable avec un message d'erreur
            return render_compte_page(request, {
                'error': "Entrée invalide"
            })

        Project.objects.create(
            p_name=name,
            p_description=desc,
            p_user=user
        )
        list_project = [Proj for Proj in Project.objects.filter(p_user=user)]
        # Message de succès réutilisant la même page
        return render_compte_page(request, {
            'success': "Projet créé avec succès",
            'list_project': list_project
        })

    return redirect('compte')

def del_project(request, project_id):
    try:
        project = Project.objects.get(p_id=project_id)
    except Project.DoesNotExist:
        return render_compte_page(request, {
            'error': "Suppression impossible! Projet non existante"
        })
    project.delete()
    return render_compte_page(request, {
            'success': "Suppression éffectuée",
        })

def add_task(request):
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("login")

        project_id = request.POST.get("task_project")
        title = request.POST.get("task_title")
        desc = request.POST.get("task_desc")
        duration_str = request.POST.get("task_duration")
        is_finished = request.POST.get("task_finish") == "on"  # Nouveau: récupérer l'état terminé

        if not project_id or not title:
            return render_compte_page(request, {"error": "Le titre et le projet sont obligatoires."})

        try:
            project = Project.objects.get(p_id=project_id, p_user=user_id)
        except Project.DoesNotExist:
            return render_compte_page(request, {"error": "Projet introuvable."})

        task = Task.objects.create(
            task_title=title,
            task_desc=desc,
            task_project=project,
            task_duration=parse_duration(duration_str) if duration_str else None,
            task_finish=is_finished,  # Nouveau: définir l'état terminé
            task_status=not is_finished  # Si terminée, alors pas active
        )

        status_message = "terminée" if is_finished else "créée"
        return render_compte_page(request, {"success": f"Tâche '{task.task_title}' {status_message} avec succès."})

def delete_task(request, task_id):
    try:
        task = Task.objects.get(task_id=task_id)
        task.delete()
        return render_compte_page(request, {"success": "Tâche supprimée avec succès."})
    except Task.DoesNotExist:
        return render_compte_page(request, {"error": "Tâche introuvable."})

# Nouvelle fonction pour basculer l'état d'une tâche
def toggle_task_status(request, task_id):
    """
    Bascule l'état terminé/non terminé d'une tâche
    """
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("login")

        try:
            # Vérifier que la tâche appartient bien à l'utilisateur connecté
            task = Task.objects.get(task_id=task_id, task_project__p_user=user_id)
            
            # Basculer l'état
            task.task_finish = not task.task_finish
            task.task_status = not task.task_finish  # Inverse de task_finish
            task.save()
            
            status_message = "marquée comme terminée" if task.task_finish else "marquée comme active"
            return render_compte_page(request, {
                "success": f"Tâche '{task.task_title}' {status_message}."
            })
            
        except Task.DoesNotExist:
            return render_compte_page(request, {
                "error": "Tâche introuvable ou accès non autorisé."
            })
    
    return redirect('compte')

# Nouvelle fonction pour marquer une tâche comme terminée (alternative)
def complete_task(request, task_id):
    """
    Marque une tâche comme terminée
    """
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("login")

        try:
            task = Task.objects.get(task_id=task_id, task_project__p_user=user_id)
            task.task_finish = True
            task.task_status = False  # Plus active si terminée
            task.save()
            
            return render_compte_page(request, {
                "success": f"Tâche '{task.task_title}' marquée comme terminée."
            })
            
        except Task.DoesNotExist:
            return render_compte_page(request, {
                "error": "Tâche introuvable ou accès non autorisé."
            })
    
    return redirect('compte')

# Nouvelle fonction pour réactiver une tâche
def reactivate_task(request, task_id):
    """
    Réactive une tâche terminée
    """
    if request.method == "POST":
        user_id = request.session.get("user_id")
        if not user_id:
            return redirect("login")

        try:
            task = Task.objects.get(task_id=task_id, task_project__p_user=user_id)
            task.task_finish = False
            task.task_status = True  # Redevient active
            task.save()
            
            return render_compte_page(request, {
                "success": f"Tâche '{task.task_title}' réactivée."
            })
            
        except Task.DoesNotExist:
            return render_compte_page(request, {
                "error": "Tâche introuvable ou accès non autorisé."
            })
    
    return redirect('compte')