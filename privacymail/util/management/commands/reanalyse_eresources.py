from django.core.management.base import BaseCommand
from mailfetcher.models import Mail
import traceback
from mailfetcher.crons.mailCrawler.analysis.leakage import (
    analyze_mail_connections_for_leakage,
)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        try:
            print("Reanalyzing Database.")
            mail_queue = Mail.objects.filter(
                processing_state=Mail.PROCESSING_STATES.DONE
            )
            print(
                '(Re-)analyzing {} mails with state "done".'.format(mail_queue.count())
            )
            count = 0
            for mail in mail_queue:
                count += 1
                for eresource in mail.eresource_set.all():
                    if eresource.mail_leakage is None:
                        continue
                    eresource.mail_leakage = None
                    eresource.save()
                analyze_mail_connections_for_leakage(mail)
                mail.processing_state = Mail.PROCESSING_STATES.DONE
                mail.save()
                mail.create_service_third_party_connections()
                if count % 20 == 0:
                    print(count)
            print("All done. Exiting.")
        except Exception:
            traceback.print_exc()

        print("Done")
