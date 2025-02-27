from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Wallet
import json

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.test_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123'
        }

    def test_user_signup(self):
        response = self.client.post(
            self.signup_url,
            data=json.dumps(self.test_user_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify user was created
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        
        # Verify wallet was created
        wallet = Wallet.objects.get(user=user)
        self.assertEqual(wallet.balance, 0)

    def test_user_login(self):
        # Create a user first
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Test login
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'username': 'testuser',
                'password': 'testpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_invalid_login(self):
        response = self.client.post(
            self.login_url,
            data=json.dumps({
                'username': 'nonexistent',
                'password': 'wrongpass'
            }),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_password_reset(self):
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Test requesting OTP
        response = self.client.post(
            reverse('request_otp'),
            data=json.dumps({'email': 'test@example.com'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        # Test password reset
        response = self.client.post(
            reverse('reset_password'),
            data=json.dumps({
                'email': 'test@example.com',
                'otp': '123456',  # This would be the actual OTP in real scenario
                'new_password': 'newpass123',
                'confirm_password': 'newpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)