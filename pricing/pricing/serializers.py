# pricing/serializers.py
from rest_framework import serializers
from .models import (
    Building, Product, Booking, Price, PriceRecommendation, PriceConfirmation
)
from django.contrib.auth.models import User


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id', 'product_id', 'room_name', 'arrival_date',
            'beds', 'room_type', 'grade', 'private_pool'
        ]


class PriceRecommendationSerializer(serializers.ModelSerializer):
    # Now that we have proper IDs, we can include product details via product_id lookup
    product_info = serializers.SerializerMethodField()

    class Meta:
        model = PriceRecommendation
        fields = [
            'id', 'product_id', 'recommended_price', 'currency',
            'created_at', 'reason', 'product_info'
        ]

    def get_product_info(self, obj):
        """Get product details by matching product_id"""
        if obj.product_id:
            try:
                product = Product.objects.get(product_id=obj.product_id)
                return {
                    'id': product.id,
                    'product_id': product.product_id,
                    'room_name': product.room_name,
                    'arrival_date': product.arrival_date,
                    'beds': product.beds,
                    'room_type': product.room_type,
                    'grade': product.grade,
                    'private_pool': product.private_pool
                }
            except Product.DoesNotExist:
                return None
        return None


class PriceConfirmationSerializer(serializers.ModelSerializer):
    recommendation = PriceRecommendationSerializer(read_only=True)
    confirmed_by = serializers.StringRelatedField()

    class Meta:
        model = PriceConfirmation
        fields = [
            'id', 'recommendation', 'confirmed_by',
            'status', 'amended_price', 'created_at',
            'written_back', 'written_back_at'
        ]
