from django.core.management.base import BaseCommand
from mailfetcher.models import Cache
from identity.models import Service
from mailfetcher.models import Thirdparty
import multiprocessing
from mailfetcher.crons.mailCrawler.createCaches import (
    create_summary_cache, create_service_cache, create_third_party_cache)
from django.db import connections
from contextlib import closing


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--no-clear',
                            action="store_true",
                            dest="no-clear",
                            help="Don't clear cache before redoing it.")

    def handle(self, *args, **options):

        if not options['no-clear']:
            Cache.clear()
            self.stdout.write("Cleared cache\n")

        create_summary_cache(force=True)
        if multiprocessing.cpu_count() > 3:
            cpus = multiprocessing.cpu_count() - 3
        else:
            cpus = 1

        print("Creating cache for services")
        with closing(multiprocessing.Pool(cpus, maxtasksperchild=1)) as p:
            p.map(multiprocessing_create_service_cache, Service.objects.all())
        connections.close_all()

        print("Creating cache for thirdparties")
        with closing(multiprocessing.Pool(cpus, maxtasksperchild=1)) as p:
            p.map(multiprocessing_create_thirdparty_cache,
                  Thirdparty.objects.all())
        print("Done")


def multiprocessing_create_service_cache(service):
    connections.close_all()
    create_service_cache(service, True)


def multiprocessing_create_thirdparty_cache(thirdparty):
    connections.close_all()
    create_third_party_cache(thirdparty, True)
