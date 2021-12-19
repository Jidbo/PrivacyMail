from django.core.management.base import BaseCommand
from mailfetcher.models import Cache


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Cache.clear()
        self.stdout.write('Cleared cache\n')
