from django.core.management.base import BaseCommand, CommandError
from mailfetcher.models import Cache
from identity.models import Service

from mailfetcher.analyser_cron import create_service_cache


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('id', nargs='+', type=int)

    def handle(self, *args, **options):
        for sid in options['id']:
            try:
                service = Service.objects.get(pk=sid)
                create_service_cache(service, True)
                Cache.get(service.derive_service_cache_path())
            except Service.DoesNotExist:
                raise CommandError('Service %s does not exist' % sid)
