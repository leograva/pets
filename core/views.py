import base64
import uuid as uuid_module

from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse

from .forms import CheckInForm, InviteTutorForm, PetForm, UserRegistrationForm
from .models import CheckIn, Pet, PetInvite


def register_view(request):
    next_url = request.POST.get('next') or request.GET.get('next') or reverse('dashboard')
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cadastro realizado com sucesso.')
            return redirect(next_url)
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form, 'next': next_url})


def login_view(request):
    next_url = request.POST.get('next') or request.GET.get('next') or reverse('dashboard')
    login_form = AuthenticationForm(request, data=request.POST or None)
    for field in login_form.fields.values():
        field.widget.attrs.setdefault('class', 'ui-input')
        field.widget.attrs.setdefault('autocomplete', 'off')

    if request.method == 'POST' and login_form.is_valid():
        user = login_form.get_user()
        login(request, user)
        return redirect(next_url)

    return render(
        request,
        'core/login.html',
        {
            'login_form': login_form,
            'next': next_url,
        },
    )


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    pets = user.pets.all()
    user_points = user.checkins.aggregate(total=Sum('points'))['total'] or 0
    recent_user_checkins = user.checkins.select_related('pet').order_by('-timestamp')[:8]

    ranking_users = get_user_model().objects.annotate(
        total_points=Sum('checkins__points')
    ).order_by('-total_points', 'username')[:10]

    ranking_pets = Pet.objects.annotate(
        total_points=Sum('checkins__points')
    ).order_by('-total_points', 'name')[:10]

    return render(
        request,
        'core/dashboard.html',
        {
            'pets': pets,
            'user_points': user_points,
            'recent_checkins': recent_user_checkins,
            'ranking_users': ranking_users,
            'ranking_pets': ranking_pets,
        },
    )


@login_required
def pet_list_view(request):
    pets = request.user.pets.prefetch_related('owners').all()
    return render(request, 'core/pet_list.html', {'pets': pets})


@login_required
def pet_detail_view(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owners=request.user)
    checkins = pet.checkins.select_related('user').order_by('-timestamp')
    invite_form = InviteTutorForm()
    invites = pet.invites.all()
    return render(
        request,
        'core/pet_detail.html',
        {
            'pet': pet,
            'checkins': checkins,
            'invite_form': invite_form,
            'invites': invites,
        },
    )


@login_required
def pet_invite_view(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owners=request.user)
    checkins = pet.checkins.select_related('user').order_by('-timestamp')
    invites = pet.invites.all()
    if request.method == 'POST':
        form = InviteTutorForm(request.POST)
        if form.is_valid():
            invitee_email = form.cleaned_data['invitee_email']
            invite = PetInvite.objects.create(
                pet=pet,
                inviter=request.user,
                invitee_email=invitee_email,
            )
            accept_url = request.build_absolute_uri(reverse('invite_accept', args=[invite.token]))

            # Render HTML email template
            html_body = render_to_string('core/email_invite.html', {
                'inviter_name': request.user.username,
                'pet_name': pet.name,
                'pet_species': pet.species,
                'accept_url': accept_url,
            })
            text_body = (
                f'Olá!\n\n'
                f'{request.user.username} convidou você para ser tutor de {pet.name} no Pets Hub.\n\n'
                f'Acesse o link abaixo para aceitar o convite:\n{accept_url}\n\n'
                f'Se você não esperava este convite, ignore este e-mail.'
            )

            email = EmailMultiAlternatives(
                subject=f'Convite para cuidar de {pet.name} — Pets Hub',
                body=text_body,
                from_email=None,  # usa DEFAULT_FROM_EMAIL do settings
                to=[invitee_email],
            )
            email.attach_alternative(html_body, 'text/html')
            email.send(fail_silently=True)

            messages.success(request, f'Convite enviado para {invitee_email}.')
            return redirect('pet_detail', pk=pet.pk)
    else:
        form = InviteTutorForm()

    return render(
        request,
        'core/pet_detail.html',
        {
            'pet': pet,
            'checkins': checkins,
            'invite_form': form,
            'invites': invites,
        },
    )


def invite_accept_view(request, token):
    invite = get_object_or_404(PetInvite, token=token)
    if invite.status != PetInvite.STATUS_PENDING:
        messages.info(request, 'Este convite já foi processado.')
        return redirect('dashboard')

    if not request.user.is_authenticated:
        return redirect(f"{reverse('login')}?next={request.path}")

    if request.user.email.lower() != invite.invitee_email.lower():
        messages.error(request, 'O e-mail do usuário autenticado não corresponde ao convite.')
        return redirect('dashboard')

    invite.accept(request.user)
    messages.success(request, f'Convite aceito! Você agora é tutor de {invite.pet.name}.')
    return redirect('pet_detail', pk=invite.pet.pk)


@login_required
def invite_delete_view(request, pk, invite_pk):
    """Remove um convite. Só o dono do pet (inviter) pode remover."""
    pet = get_object_or_404(Pet, pk=pk, owners=request.user)
    invite = get_object_or_404(PetInvite, pk=invite_pk, pet=pet)

    if request.method == 'POST':
        invite.delete()
        messages.success(request, f'Convite para {invite.invitee_email} removido.')

    return redirect('pet_detail', pk=pet.pk)


@login_required
def pet_create_view(request):
    if request.method == 'POST':
        form = PetForm(request.POST)
        if form.is_valid():
            pet = form.save()
            pet.owners.add(request.user)
            messages.success(request, 'Pet cadastrado com sucesso.')
            return redirect('pet_detail', pk=pet.pk)
    else:
        form = PetForm()
    return render(request, 'core/pet_form.html', {'form': form, 'title': 'Cadastrar pet'})


@login_required
def pet_update_view(request, pk):
    pet = get_object_or_404(Pet, pk=pk, owners=request.user)
    if request.method == 'POST':
        form = PetForm(request.POST, instance=pet)
        if form.is_valid():
            pet = form.save()
            if request.user not in pet.owners.all():
                pet.owners.add(request.user)
            messages.success(request, 'Dados do pet atualizados.')
            return redirect('pet_detail', pk=pet.pk)
    else:
        form = PetForm(instance=pet)
    return render(request, 'core/pet_form.html', {'form': form, 'title': 'Editar pet'})


@login_required
def checkin_select_pet_view(request):
    pets = request.user.pets.order_by('name').all()
    return render(request, 'core/checkin_select_pet.html', {'pets': pets})


@login_required
def checkin_create_view(request, pet_id):
    pet = get_object_or_404(Pet, pk=pet_id, owners=request.user)
    if request.method == 'POST':
        form = CheckInForm(request.POST)
        if form.is_valid():
            checkin = form.save(commit=False)
            checkin.pet = pet
            checkin.user = request.user

            # Handle base64 photo from camera capture
            photo_data = request.POST.get('photo_data', '').strip()
            if photo_data and photo_data.startswith('data:image/'):
                try:
                    header, encoded = photo_data.split(',', 1)
                    ext = 'jpg' if 'jpeg' in header else 'png'
                    filename = f'checkin_{uuid_module.uuid4().hex}.{ext}'
                    checkin.photo.save(filename, ContentFile(base64.b64decode(encoded)), save=False)
                except Exception:
                    pass  # foto inválida — ignora e salva sem foto

            checkin.save()
            messages.success(request, 'Check-in registrado com sucesso.')
            return redirect('pet_detail', pk=pet.pk)
    else:
        form = CheckInForm()
    return render(request, 'core/checkin_form.html', {'form': form, 'pet': pet})
