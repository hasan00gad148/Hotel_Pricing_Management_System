# django_app/pricing/models.py
from django.db import models
from django.contrib.auth.models import User

CURRENCY_CHOICES = [
    ('USD','USD'), ('EUR','EUR'), ('EGP','EGP'), ('GBP','GBP')
]

class Building(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self): return self.name

class Product(models.Model):
    product_id = models.IntegerField(blank=True, null=True)
    room_name = models.TextField(blank=True, null=True)
    arrival_date = models.DateField(blank=True, null=True)
    beds = models.IntegerField(blank=True, null=True)
    room_type = models.TextField(blank=True, null=True)
    grade = models.IntegerField(blank=True, null=True)
    private_pool = models.BooleanField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['arrival_date','room_type','beds','grade','private_pool']),
        ]

    def __str__(self): return f"{self.product_id} - {self.room_name}"

class Booking(models.Model):
    booking_id = models.CharField(max_length=128, unique=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bookings')
    creation_date = models.DateTimeField()
    confirmation_status = models.CharField(max_length=50)  # e.g. confirmed/cancelled
    arrival_date = models.DateField()

class Price(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='prices')
    currency = models.CharField(max_length=8, choices=CURRENCY_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product','currency')

class PriceRecommendation(models.Model):
    product_id = models.IntegerField(blank=True, null=True)
    recommended_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=8, choices=CURRENCY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)

class PriceConfirmation(models.Model):
    REJECTED = 'rejected'
    ACCEPTED = 'accepted'
    AMENDED = 'amended'
    PENDING = 'pending'
    STATUS_CHOICES = [(PENDING,'pending'), (ACCEPTED,'accepted'), (AMENDED,'amended'), (REJECTED,'rejected')]

    recommendation = models.ForeignKey(PriceRecommendation, on_delete=models.CASCADE, related_name='confirmations')
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    amended_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
# change to PriceConfirmation model
    written_back = models.BooleanField(default=False)
    written_back_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['status','created_at'])]
