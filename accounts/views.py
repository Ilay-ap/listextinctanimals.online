from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils.translation import get_language, activate, gettext_lazy as _
from .models import UserProfile


def register_view(request):
    """View para registro de novos usuários"""
    if request.user.is_authenticated:
        return redirect('mammals:index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validações
        if not username or not email or not password:
            messages.error(request, _('Please fill in all fields.'))
            return render(request, 'accounts/register.html')
        
        if password != password_confirm:
            messages.error(request, _('Passwords do not match.'))
            return render(request, 'accounts/register.html')
        
        if len(password) < 6:
            messages.error(request, _('Password must be at least 6 characters.'))
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, _('This username is already in use.'))
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, _('This email is already registered.'))
            return render(request, 'accounts/register.html')
        
        # Criar usuário
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Criar perfil (get_or_create para evitar duplicação)
            UserProfile.objects.get_or_create(user=user, defaults={'is_admin': False})
            
            # Salvar idioma atual antes do login
            current_language = get_language()
            
            # Fazer login automático
            login(request, user)
            
            # Restaurar idioma após login
            activate(current_language)
            request.session['django_language'] = current_language
            
            messages.success(request, _('Welcome, %(username)s! Your account was created successfully.') % {'username': username})
            return redirect('mammals:index')
        
        except Exception as e:
            messages.error(request, _('Error creating account: %(error)s') % {'error': str(e)})
            return render(request, 'accounts/register.html')
    
    return render(request, 'accounts/register.html')


def login_view(request):
    """View para login de usuários"""
    if request.user.is_authenticated:
        return redirect('mammals:index')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember', False)
        
        if not username or not password:
            messages.error(request, _('Please fill in all fields.'))
            return render(request, 'accounts/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Salvar idioma atual antes do login
            current_language = get_language()
            
            login(request, user)
            
            # Restaurar idioma após login
            activate(current_language)
            request.session['django_language'] = current_language
            
            # Configurar duração da sessão
            if not remember:
                request.session.set_expiry(0)  # Expira ao fechar o navegador
            
            messages.success(request, _('Welcome, %(username)s!') % {'username': user.username})
            
            # Redirecionar para a página solicitada ou para o index
            next_page = request.GET.get('next', 'mammals:index')
            return redirect(next_page)
        else:
            messages.error(request, _('Incorrect username or password.'))
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """View para logout de usuários"""
    # Salvar idioma atual antes do logout
    current_language = get_language()
    
    logout(request)
    
    # Restaurar idioma após logout
    activate(current_language)
    request.session['django_language'] = current_language
    
    messages.info(request, _('You have been logged out.'))
    return redirect('mammals:index')


@login_required
def profile_view(request):
    """View para visualizar perfil do usuário"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    context = {
        'user_profile': user_profile,
        'comment_count': request.user.comments.count(),
        'favorite_count': request.user.favorites.count(),
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """View para editar perfil do usuário"""
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        new_password_confirm = request.POST.get('new_password_confirm', '')
        
        # Validar username
        if username != request.user.username:
            if User.objects.filter(username=username).exists():
                messages.error(request, _('This username is already in use.'))
                return render(request, 'accounts/edit_profile.html')
            request.user.username = username
        
        # Validar email
        if email != request.user.email:
            if User.objects.filter(email=email).exists():
                messages.error(request, _('This email is already registered.'))
                return render(request, 'accounts/edit_profile.html')
            request.user.email = email
        
        # Alterar senha se fornecida
        if new_password:
            if not current_password:
                messages.error(request, _('Please enter your current password.'))
                return render(request, 'accounts/edit_profile.html')
            
            if not request.user.check_password(current_password):
                messages.error(request, _('Incorrect current password.'))
                return render(request, 'accounts/edit_profile.html')
            
            if new_password != new_password_confirm:
                messages.error(request, _('New passwords do not match.'))
                return render(request, 'accounts/edit_profile.html')
            
            if len(new_password) < 6:
                messages.error(request, _('New password must be at least 6 characters.'))
                return render(request, 'accounts/edit_profile.html')
            
            request.user.set_password(new_password)
        
        try:
            request.user.save()
            messages.success(request, _('Profile updated successfully!'))
            return redirect('accounts:profile')
        except Exception as e:
            messages.error(request, _('Error updating profile: %(error)s') % {'error': str(e)})
    
    return render(request, 'accounts/edit_profile.html')
