# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User

CURRENCY_CHOICES = [
    ('USD','USD'), ('EUR','EUR'), ('EGP','EGP'), ('GBP','GBP')
]




class Booking(models.Model):
    id = models.IntegerField()
    booking_id = models.IntegerField(blank=True, null=True)
    product_id = models.IntegerField(blank=True, null=True)
    creation_date = models.DateField(blank=True, null=True)
    confirmation_status = models.TextField(blank=True, null=True)
    arrival_date = models.DateField(blank=True, null=True)

    class Meta:
        app_label = 'pricing'
        db_table = 'pricing_booking'


class Building(models.Model):
    id = models.IntegerField()
    name = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'pricing'
        db_table = 'pricing_building'


class Price(models.Model):
    id = models.IntegerField()
    product_id = models.IntegerField(blank=True, null=True)
    currency = models.TextField(blank=True, null=True)
    value = models.FloatField(blank=True, null=True)
    updated_at = models.DateTimeField()

    class Meta:
        app_label = 'pricing'
        db_table = 'pricing_price'


class PriceRecommendation(models.Model):
    id = models.IntegerField()
    product_id = models.IntegerField(blank=True, null=True)
    recommended_price = models.FloatField(blank=True, null=True)
    currency = models.TextField()
    created_at = models.DateTimeField()
    reason = models.TextField()

    class Meta:
        app_label = 'pricing'
        db_table = 'pricing_pricerecommendation'


class Product(models.Model):
    id = models.IntegerField()
    product_id = models.IntegerField(blank=True, null=True)
    room_name = models.TextField(blank=True, null=True)
    arrival_date = models.DateField(blank=True, null=True)
    beds = models.IntegerField(blank=True, null=True)
    room_type = models.TextField(blank=True, null=True)
    grade = models.IntegerField(blank=True, null=True)
    private_pool = models.BooleanField(blank=True, null=True)

    class Meta:
        app_label = 'pricing'
        db_table = 'pricing_product'


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
        app_label = 'pricing'



