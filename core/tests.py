from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import CheckIn, Pet, PetInvite


class CoreModelsTests(TestCase):
    def test_pet_can_have_multiple_owners(self):
        user1 = get_user_model().objects.create_user(username='user1', password='pass')
        user2 = get_user_model().objects.create_user(username='user2', password='pass')
        pet = Pet.objects.create(name='Scooby')
        pet.owners.set([user1, user2])
        self.assertEqual(pet.owners.count(), 2)

    def test_checkin_points_are_assigned(self):
        user = get_user_model().objects.create_user(username='user1', password='pass')
        pet = Pet.objects.create(name='Buddy')
        pet.owners.add(user)
        checkin = CheckIn.objects.create(pet=pet, user=user, checkin_type=CheckIn.WALK)
        self.assertEqual(checkin.points, 8)


class CoreViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='test', password='pass')

    def test_register_and_login(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_login_page_contains_login_form(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'Entrar')
        self.assertContains(response, 'Não tem conta?')


class CoreInviteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='owner', email='owner@example.com', password='pass')
        self.invitee = get_user_model().objects.create_user(username='guest', email='guest@example.com', password='pass')
        self.pet = Pet.objects.create(name='Buddy')
        self.pet.owners.add(self.user)

    def test_invite_creation(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('pet_invite', args=[self.pet.pk]), {'invitee_email': 'guest@example.com'})
        self.assertEqual(response.status_code, 302)
        invite = PetInvite.objects.get(pet=self.pet, invitee_email='guest@example.com')
        self.assertEqual(invite.status, PetInvite.STATUS_PENDING)

    def test_invite_accept_by_matching_email(self):
        invite = PetInvite.objects.create(pet=self.pet, inviter=self.user, invitee_email='guest@example.com')
        self.client.force_login(self.invitee)
        response = self.client.get(reverse('invite_accept', args=[invite.token]))
        self.assertRedirects(response, reverse('pet_detail', args=[self.pet.pk]))
        invite.refresh_from_db()
        self.assertEqual(invite.status, PetInvite.STATUS_ACCEPTED)
        self.assertIn(self.invitee, self.pet.owners.all())
