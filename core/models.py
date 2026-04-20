import uuid

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Pet(models.Model):
    name = models.CharField(max_length=120)
    species = models.CharField(max_length=80, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='pets')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def total_points(self):
        return self.checkins.aggregate(total=Sum('points'))['total'] or 0

    def recent_checkins(self):
        return self.checkins.order_by('-timestamp')[:5]


class CheckIn(models.Model):
    FOOD = 'food'
    WALK = 'walk'
    VET = 'vet'
    MEDICATION = 'medication'
    VACINE = 'vacine'
    OTHER = 'other'

    TYPE_CHOICES = [
        (FOOD, 'Alimentação'),
        (WALK, 'Passeio'),
        (VET, 'Veterinário'),
        (MEDICATION, 'Medicação'),
        (VACINE, 'Vacinação'),
        (OTHER, 'Outros'),
    ]

    TYPE_POINTS = {
        FOOD: 5,
        WALK: 8,
        VET: 12,
        MEDICATION: 10,
        VACINE:15,
        OTHER: 2,
        
    }

    pet = models.ForeignKey(Pet, related_name='checkins', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='checkins', on_delete=models.CASCADE)
    checkin_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    description = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=0)
    photo = models.ImageField(upload_to='checkins/', blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.get_checkin_type_display()} — {self.pet.name}'

    def save(self, *args, **kwargs):
        self.points = self.TYPE_POINTS.get(self.checkin_type, 0)
        super().save(*args, **kwargs)


class PetInvite(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pendente'),
        (STATUS_ACCEPTED, 'Aceito'),
        (STATUS_CANCELLED, 'Cancelado'),
    ]

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    pet = models.ForeignKey(Pet, related_name='invites', on_delete=models.CASCADE)
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_pet_invites', on_delete=models.CASCADE)
    invitee_email = models.EmailField()
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=STATUS_PENDING)
    accepted_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='accepted_pet_invites', null=True, blank=True, on_delete=models.SET_NULL)
    accepted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Convite para {self.invitee_email} ({self.pet.name})'

    def accept(self, user):
        if self.status != self.STATUS_PENDING:
            return
        self.pet.owners.add(user)
        self.status = self.STATUS_ACCEPTED
        self.accepted_by = user
        self.accepted_at = timezone.now()
        self.save()
