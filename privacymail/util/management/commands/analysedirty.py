from django.core.management.base import BaseCommand
from mailfetcher.models import Cache
from mailfetcher.analyser_cron import analyse_dirty_services


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        Cache.clear()
        self.stdout.write("Analysing dirty Services\n")

        analyse_dirty_services()

        print("Done")
