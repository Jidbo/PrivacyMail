from django.core.management.base import BaseCommand
from django.core.cache import cache
from mailfetcher.analyser_cron import analyse_dirty_services


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        cache.clear()
        self.stdout.write("Analysing dirty Services\n")

        analyse_dirty_services()

        print("Done")
