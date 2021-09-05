from django.core.management.base import BaseCommand
from identity.models import Service
from mailfetcher.analyser_cron import create_service_cache
import time


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        print("Services")
        t = time.time()
        service1 = Service.objects.filter(id=1)[0]
        # print(service1.mails_not_cached().count()
        create_service_cache(service1, force=True)
        t2 = time.time()
        print(t2-t)
        print('Done')
