# pricing/management/commands/writeback_confirmed_prices.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from pricing.models import PriceConfirmation, Price
from decimal import Decimal

class Command(BaseCommand):
    help = "Write back accepted or amended prices to the Prices table / external system. Only pending writebacks will be processed."

    def handle(self, *args, **options):
        # Select confirmations that are accepted or amended and not yet written back
        confirmations = PriceConfirmation.objects.select_related('recommendation__product').filter(
            status__in=[PriceConfirmation.ACCEPTED, PriceConfirmation.AMENDED],
            written_back=False
        ).order_by('created_at')

        count = 0
        for cf in confirmations:
            try:
                with transaction.atomic():
                    product = cf.recommendation.product
                    currency = cf.recommendation.currency
                    new_price = None
                    if cf.status == PriceConfirmation.ACCEPTED:
                        new_price = cf.recommendation.recommended_price
                    elif cf.status == PriceConfirmation.AMENDED and cf.amended_price is not None:
                        new_price = cf.amended_price
                    else:
                        # skip if amended but no amended price provided
                        self.stdout.write(self.style.WARNING(f"Skipping CF {cf.id}: no price to write back"))
                        continue

                    # Update or create Price record
                    Price.objects.update_or_create(
                        product=product,
                        currency=currency,
                        defaults={'value': Decimal(new_price)}
                    )

                    # Optionally: call external API here to write the price to the hotel's internal system
                    # simulate_external_writeback(product, currency, new_price)

                    cf.written_back = True
                    cf.written_back_at = timezone.now()
                    cf.save(update_fields=['written_back','written_back_at'])
                    count += 1
                    self.stdout.write(self.style.SUCCESS(f"Wrote back price for product {product.product_id} - {currency} {new_price} (cf={cf.id})"))

            except Exception as e:
                self.stderr.write(f"Failed to writeback cf={cf.id}: {str(e)}")
        self.stdout.write(self.style.SUCCESS(f"Done. total written back: {count}"))
