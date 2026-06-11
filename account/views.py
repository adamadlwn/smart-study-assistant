from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.contrib.auth.models import User


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Kalau ada ?next=, redirect ke sana. Kalau tidak, ke dashboard
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Username atau password salah.')

    return render(request, 'account/login.html')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Password tidak cocok.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username sudah digunakan.')
        elif len(password1) < 8:
            messages.error(request, 'Password minimal 8 karakter.')
        else:
            user = User.objects.create_user(username=username, password=password1)
            user.save()
            messages.success(request, 'Akun berhasil dibuat! Silakan login.')
            return redirect('account_ready')

    return render(request, 'account/register.html')


def account_ready(request):
    return render(request, 'account/account_ready.html')


def logout_view(request):
    logout(request)
    return redirect('login')