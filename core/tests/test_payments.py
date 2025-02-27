from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import Wallet, Transaction
from decimal import Decimal
import json

class PaymentTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.wallet = Wallet.objects.get(user=self.user)
        self.client.login(username='testuser', password='testpass123')

    def test_initiate_payment(self):
        response = self.client.post(
            reverse('initiate_payment'),
            data=json.dumps({
                'amount': '1000',
                'payment_gateway': 'paystack'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('redirect_url', data)

    def test_wallet_credit(self):
        initial_balance = self.wallet.balance
        amount = Decimal('1000.00')
        
        # Create a transaction
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            amount=amount,
            type='credit',
            payment_gateway='paystack',
            payment_reference='test_ref_123'
        )
        
        # Credit wallet
        self.wallet.credit(amount, transaction)
        self.wallet.refresh_from_db()
        
        # Verify balance increased
        self.assertEqual(self.wallet.balance, initial_balance + amount)

    def test_manual_payment(self):
        # Test manual payment initiation
        response = self.client.get(
            reverse('manual_payment', args=['test_ref_123'])
        )
        self.assertEqual(response.status_code, 200)
        
        # Test manual payment confirmation
        response = self.client.post(
            reverse('confirm_manual_payment'),
            data=json.dumps({
                'reference': 'test_ref_123',
                'proof_of_payment': 'test_proof.jpg'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

    def test_payment_gateway_limits(self):
        # Test amount below minimum
        response = self.client.post(
            reverse('initiate_payment'),
            data=json.dumps({
                'amount': '50',  # Below minimum of 100 Naira
                'payment_gateway': 'paystack'
            }),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertFalse(data['success'])

        # Test amount above maximum
        response = self.client.post(
            reverse('initiate_payment'),
            data=json.dumps({
                'amount': '20000000',  # Above maximum
                'payment_gateway': 'paystack'
            }),
            content_type='application/json'
        )
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_transaction_history(self):
        # Create some test transactions
        Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('1000.00'),
            type='credit',
            payment_gateway='paystack',
            payment_reference='test_ref_1'
        )
        Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('500.00'),
            type='credit',
            payment_gateway='flutterwave',
            payment_reference='test_ref_2'
        )

        # Test transaction history view
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'test_ref_1')
        self.assertContains(response, 'test_ref_2')

    def test_transaction_status_update(self):
        # Create a pending transaction
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('1000.00'),
            type='credit',
            payment_gateway='manual',
            payment_reference='test_ref_status',
            status='pending'
        )

        # Update transaction status to success
        transaction.status = 'success'
        transaction.save()

        # Verify wallet balance is updated
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('1000.00'))

    def test_flutterwave_payment(self):
        response = self.client.post(
            reverse('initiate_payment'),
            data=json.dumps({
                'amount': '1000',
                'gateway': 'flutterwave'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

    def test_display_amount(self):
        transaction = Transaction.objects.create(
            wallet=self.wallet,
            amount=Decimal('1000000.00'),
            type='credit',
            payment_gateway='paystack',
            payment_reference='test_ref_display'
        )
        self.assertEqual(transaction.display_amount, '1.0M')