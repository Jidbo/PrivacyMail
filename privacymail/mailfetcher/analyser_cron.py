import traceback
import logging
from django_cron import CronJobBase, Schedule
from django.db import connections
from datetime import date
from mailfetcher.crons.mailCrawler.createCaches import create_service_cache
from identity.models import Identity, Service
from multiprocessing import cpu_count, Pool
from contextlib import closing
from mailfetcher.models import Mail

LONG_SEPERATOR = "##########################################################"

logger = logging.getLogger(__name__)


def analyse_dirty_service(dirty_service):
    connections.close_all()
    dirty_service.set_has_approved_identity()
    print(dirty_service)
    mark_idents_as_dead(dirty_service)
    analyze_differences_between_similar_mails(dirty_service)
    dirty_service.resultsdirty = False
    dirty_service.save()
    create_service_cache(dirty_service, False)


def analyse_dirty_services():
    # Re-generate caches for services with updated data
    dirty_services = Service.objects.filter(resultsdirty=True)
    print(dirty_services.count())
    if cpu_count() > 5:
        cpus = cpu_count() - 5
    else:
        cpus = 1

    with closing(Pool(cpus, maxtasksperchild=1)) as p:
        p.map(analyse_dirty_service, dirty_services)


class Analyser(CronJobBase):
    RUN_EVERY_MINS = 2 * 60  # every 2 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = "org.privacy-mail.analyser"  # a unique code

    # ser = Service.objects.get(pk=1)
    # tp = Thirdparty.objects.get(pk=1)
    # embedding = ServiceThirdPartyEmbeds.objects.create(
    #     service=ser, thirdparty=tp)
    def do(self):

        try:
            analyse_dirty_services()
            # address_leakage_statistics()
        except Exception as e:
            logger.error(
                "AnalyserCron: Exception encoutered: %s" %
                e.__class__.__name__,
                exc_info=True,
            )
            traceback.print_exc()


# analyze one mail in more detail.
def analyze_differences_between_similar_mails(service):
    """
    Compares similar mails of a service.
    :param service: Which service to analyse.
    :return: num_pairs, ratio (personalised-/all links), minimum, maximum, mean, median
    """
    # counter = 0
    already_processed_mails = {}
    # mail_set = Mail.objects.all()
    mail_set = service.mails_similarity_not_processed()
    # service_mail_metrics = {}
    pairs_analysed = 0
    for m in mail_set:
        # TODO look for pairs instead of single mails, that have already been processed
        if m.id in already_processed_mails:
            continue
        already_processed_mails[m.id] = True
        m.similarity_processed = True
        m.save()
        identity = m.identity.all()
        if identity.count() > 0:
            identity = identity[0]
        else:
            logger.info("No associated identity with mail.",
                        extra={"MailId": m.id})
            print("No associated identity with mail: {}".format(m.id))
            continue
        # service = identity.service.name
        # results = {}
        # print(m)
        similar_mails = m.get_similar_mails_of_different_identities()
        if len(similar_mails) == 0:
            continue
        for el in similar_mails:
            # if el.id in already_processed_mails:
            #     continue
            pairs_analysed += 1
            already_processed_mails[el.id] = True
            # print(el)
            difference_measure, _ = m.compare_text_of_mails(el)
            # print(difference_measure)
            # if difference_measure < 0.9993:
            if difference_measure < 0.985:
                # logger.warning('Possible A/B testing', extra={'ID first mail': m.id, 'ID second mail': el.id,
                #                                               'differences': differences})
                m.possible_AB_testing = True
                m.save()
                el.possible_AB_testing = True
                el.save()
                continue
            else:
                m.get_similar_links(el)


def mark_idents_as_dead(service):
    idents = Identity.objects.filter(service=service)
    last_5_mail_date = date.min

    for identity in idents:
        identity_mails = Mail.objects.filter(
            identity=identity).distinct().order_by("-date_time")

        if len(identity_mails) >= 5:
            date_time = identity_mails[4].date_time.date()

            if date_time > last_5_mail_date:
                last_5_mail_date = date_time

    for identity in idents:
        identity_mails = Mail.objects.filter(
            identity=identity).distinct().order_by("-date_time")

        if len(identity_mails) > 0:
            try:
                last_mail_date = identity_mails.first().date_time.date()
            except AttributeError:
                identity.mark_as_dead()
                return

            if last_mail_date < last_5_mail_date:
                identity.mark_as_dead()
            else:
                identity.resurrect()
