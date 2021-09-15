from django.core.management.base import BaseCommand, CommandError
from mailfetcher.models import Mail
from mailfetcher.crons.mailCrawler.openWPM import analyzeSingleMail


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('id',
                            nargs='+',
                            type=int,
                            help='Id of mail to analyze')

    def handle(self, *args, **options):
        mail_id = options['id'][0]
        try:
            mail = Mail.objects.get(pk=mail_id).raw
        except Mail.DoesNotExist:
            raise CommandError('Mail %s does not exist' % mail_id)

        analyzeSingleMail(mail)
        print("Done")
