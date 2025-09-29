# generate_mock_data.py
import os
import django
import random
from decimal import Decimal
from datetime import date, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pricing.settings")
django.setup()


from django.contrib.auth.models import User, Group


def create_groups_and_users():
    """Create demo groups and users"""
    for g in ['pricing_manager', 'regional_manager', 'reporting_user']:
        Group.objects.get_or_create(name=g)

    if not User.objects.filter(username="manager").exists():
        user = User.objects.create_user(username="manager", password="manager123")
        user.groups.add(Group.objects.get(name='pricing_manager'))
        print("✅ Created pricing_manager user (username=manager, password=manager123)")

    if not User.objects.filter(username="reporter").exists():
        user = User.objects.create_user(username="reporter", password="reporter123")
        user.groups.add(Group.objects.get(name='reporting_user'))
        print("✅ Created reporting_user (username=reporter, password=reporter123)")



if __name__ == "__main__":
    create_groups_and_users()
