from django.core.management.base import BaseCommand
from mailfetcher.models import Cache


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Cache.delete('onDemand_analysis_queue')
        print("Done")
