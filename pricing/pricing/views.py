

# pricing/views.py
from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db import transaction
from .models import (
    Building, Product, PriceRecommendation, PriceConfirmation
)
from .serializers import (
    BuildingSerializer, ProductSerializer,
    PriceRecommendationSerializer, PriceConfirmationSerializer
)
from .permissions import IsPricingManager


# 🔹 Filters endpoint
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_filter_definitions(request):
    filters = [
        {
            'name': 'building',
            'type': 'dropdown',
            'field': 'building',
            'options': list(Building.objects.values_list('name', flat=True).distinct())
        },
        {
            'name': 'room_type',
            'type': 'dropdown',
            'field': 'room_type',
            'options': list(Product.objects.exclude(room_type__isnull=True).exclude(room_type__exact='').values_list('room_type', flat=True).distinct())
        },
        {
            'name': 'beds',
            'type': 'dropdown',
            'field': 'beds',
            'options': list(Product.objects.exclude(beds__isnull=True).values_list('beds', flat=True).distinct().order_by('beds'))
        },
        {
            'name': 'arrival_date',
            'type': 'date',
            'field': 'arrival_date'
        }
    ]
    return Response(filters)


# 🔹 Recommendation List View
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'


class RecommendationListView(generics.ListAPIView):
    serializer_class = PriceRecommendationSerializer
    pagination_class = StandardPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Base queryset with proper ordering
        queryset = PriceRecommendation.objects.all().order_by('-created_at')

        # Get filter parameters
        building = self.request.query_params.get('building')
        room_type = self.request.query_params.get('room_type')
        beds = self.request.query_params.get('beds')
        arrival_date = self.request.query_params.get('arrival_date')

        # Filter based on product properties
        if any([room_type, beds, arrival_date]):
            product_filters = {}
            
            if room_type:
                product_filters['room_type'] = room_type
            if beds:
                try:
                    product_filters['beds'] = int(beds)
                except (ValueError, TypeError):
                    pass
            if arrival_date:
                product_filters['arrival_date'] = arrival_date

            # Get matching product_ids from Product table
            if product_filters:
                matching_product_ids = list(
                    Product.objects.filter(**product_filters).values_list('product_id', flat=True)
                )
                queryset = queryset.filter(product_id__in=matching_product_ids)

        # Building filter - for now skip since Product doesn't have building relationship
        # You could implement this if you create the building-product relationship
        if building:
            # This would work if you have building as ForeignKey in Product model
            # matching_product_ids = list(
            #     Product.objects.filter(building__name=building).values_list('product_id', flat=True)
            # )
            # queryset = queryset.filter(product_id__in=matching_product_ids)
            pass

        return queryset


# 🔹 Batch Confirm View
class BatchConfirmView(APIView):
    permission_classes = [IsPricingManager]

    @transaction.atomic
    def post(self, request):
        """
        Expected payload:
        {
          "confirmations": [
            {"recommendation_id": 1, "status": "accepted"},
            {"recommendation_id": 2, "status": "amended", "amended_price": 120.00}
          ]
        }
        """
        confirmations_data = request.data.get('confirmations', [])
        
        if not confirmations_data:
            return Response(
                {"error": "No confirmations provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        results = []

        for item in confirmations_data:
            rec_id = item.get('recommendation_id')
            status_val = item.get('status')
            amended_price = item.get('amended_price')

            if not rec_id:
                results.append({
                    "recommendation_id": rec_id,
                    "status": "failed",
                    "error": "Missing recommendation_id"
                })
                continue

            try:
                # Now we can use proper Django ID lookup
                recommendation = PriceRecommendation.objects.get(id=rec_id)

                # Validate status against model choices
                valid_statuses = [choice[0] for choice in PriceConfirmation.STATUS_CHOICES]
                if status_val not in valid_statuses:
                    results.append({
                        "recommendation_id": rec_id,
                        "status": "failed",
                        "error": f"Invalid status '{status_val}'. Valid options: {valid_statuses}"
                    })
                    continue

                # For amended status, require amended_price
                if status_val == PriceConfirmation.AMENDED and not amended_price:
                    results.append({
                        "recommendation_id": rec_id,
                        "status": "failed",
                        "error": "amended_price is required when status is 'amended'"
                    })
                    continue

                # Check if recommendation already has a confirmation
                existing_confirmation = PriceConfirmation.objects.filter(
                    recommendation=recommendation
                ).first()

                if existing_confirmation:
                    # Update existing confirmation
                    existing_confirmation.status = status_val
                    existing_confirmation.amended_price = amended_price if status_val == PriceConfirmation.AMENDED else None
                    existing_confirmation.confirmed_by = request.user
                    existing_confirmation.save()
                    confirmation = existing_confirmation
                else:
                    # Create new confirmation
                    confirmation = PriceConfirmation.objects.create(
                        recommendation=recommendation,
                        confirmed_by=request.user,
                        status=status_val,
                        amended_price=amended_price if status_val == PriceConfirmation.AMENDED else None
                    )

                results.append({
                    "recommendation_id": rec_id,
                    "confirmation_id": confirmation.id,
                    "status": "success"
                })

            except PriceRecommendation.DoesNotExist:
                results.append({
                    "recommendation_id": rec_id,
                    "status": "failed",
                    "error": "Recommendation not found"
                })
            except Exception as e:
                results.append({
                    "recommendation_id": rec_id,
                    "status": "failed",
                    "error": str(e)
                })

        return Response({"results": results}, status=status.HTTP_207_MULTI_STATUS)