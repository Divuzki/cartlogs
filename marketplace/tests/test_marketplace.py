from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from marketplace.models import SocialMediaAccount, CartSession, Order, Log
from core.models import Wallet
from decimal import Decimal
import json

class MarketplaceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.wallet = Wallet.objects.get(user=self.user)
        self.client.login(username='testuser', password='testpass123')
        
        # Create test social media account
        self.account = SocialMediaAccount.objects.create(
            title='Test Account',
            social_media='twitter',
            price=Decimal('1000.00'),
            followers_count=1000,
            account_age='1-2 years'
        )

    def test_marketplace_listing(self):
        response = self.client.get(reverse('marketplace:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Account')
        self.assertContains(response, 'twitter')

    def test_add_to_cart(self):
        response = self.client.post(
            reverse('marketplace:add_to_cart'),
            data=json.dumps({
                'account_id': self.account.id
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify cart session was created
        cart = CartSession.objects.filter(account=self.account).first()
        self.assertIsNotNone(cart)

    def test_checkout_process(self):
        # Add funds to wallet first
        self.wallet.balance = Decimal('2000.00')
        self.wallet.save()
        
        # Add item to cart
        cart = CartSession.objects.create(account=self.account)
        
        # Test checkout
        response = self.client.post(
            reverse('marketplace:checkout'),
            data=json.dumps({
                'cart_ids': [cart.id]
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify order was created
        order = Order.objects.filter(user=self.user).first()
        self.assertIsNotNone(order)
        
        # Verify wallet was debited
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))

    def test_order_history(self):
        # Create a test order
        order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('1000.00')
        )
        Log.objects.create(
            order=order,
            account=self.account,
            credentials='{"username": "test", "password": "test123"}'
        )
        
        # Test order history view
        response = self.client.get(reverse('marketplace:orders'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Account')

    def test_view_all_accounts(self):
        response = self.client.get(reverse('marketplace:view_all'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Account')

    def test_insufficient_balance_checkout(self):
        # Set wallet balance to 0
        self.wallet.balance = Decimal('0.00')
        self.wallet.save()
        
        # Add item to cart
        cart = CartSession.objects.create(account=self.account)
        
        # Test checkout with insufficient balance
        response = self.client.post(
            reverse('marketplace:checkout'),
            data=json.dumps({
                'cart_ids': [cart.id]
            }),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('insufficient balance', data.get('error', '').lower())