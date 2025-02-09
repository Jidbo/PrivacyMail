from django.views.generic import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from identity.util import validate_domain
from django.conf import settings
from mailfetcher.models import Cache
from identity.models import Identity, Service
from mailfetcher.analyser_cron import create_service_cache
from mailfetcher.crons.mailCrawler.openWPM import analyzeSingleMail
from django.http import HttpResponse
import json
import logging
from random import shuffle
import uuid

logger = logging.getLogger(__name__)


class BookmarkletApiView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(BookmarkletApiView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            url = request.POST["url"]
            url = validate_domain(url)

            # Get or create the service matching this domain
            service, created = Service.get_or_create(url=url, name=url)
            service.save()

            # Select a domain to use for the identity
            # Create a list of possible domains
            domains = [cred["DOMAIN"] for cred in settings.MAILCREDENTIALS]
            # Shuffle it
            shuffle(domains)
            # Iterate through it
            for identityDomain in domains:
                # If the domain has not yet been used, stop the loop, otherwise try the next
                if (
                    Identity.objects.filter(service_id=service.pk)
                    .filter(mail__contains=identityDomain)
                    .count()
                    == 0
                ):
                    break
            # At this point, we have either selected a domain that has not yet been used for the
            # provided service, or the service already has at least one identity for each domain,
            # in which case we have picked one domain at random (by shuffling the list first).

            # Create an identity and save it
            ident = Identity.create(service, identityDomain)
            ident.save()

            if created:
                create_service_cache(service, force=True)

            # Return the created identity
            r = JsonResponse(
                {
                    "site": url,
                    "email": ident.mail,
                    "first": ident.first_name,
                    "last": ident.surname,
                    "gender": "Male" if ident.gender else "Female",
                }
            )
        except KeyError:
            logger.warning(
                "BookmarkletApiView.post: Malformed request received, missing url.",
                extra={"request": request},
            )
            r = JsonResponse({"error": "No URL passed"})
        except AssertionError:
            # Invalid URL passed
            logger.warning(
                "BookmarkletApiView.post: Malformed request received, malformed URL.",
                extra={"request": request},
            )
            r = JsonResponse({"error": "Invalid URL passed."})
        r["Access-Control-Allow-Origin"] = "*"
        return r


class AnalysisView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(AnalysisView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        queue = Cache.get("onDemand_analysis_queue")
        if queue is None:
            queue = {}
        print(settings.MAXIMUM_ALLOWED_EMAIL_ANALYSIS_ONDEMAND)
        if len(queue) >= settings.MAXIMUM_ALLOWED_EMAIL_ANALYSIS_ONDEMAND:
            return HttpResponse(status=503)
        else:
            analysis_id = str(uuid.uuid4())
            queue[analysis_id] = analysis_id
            Cache.set("onDemand_analysis_queue", queue)
            try:
                body_unicode = request.body.decode("utf-8")
                body_json = json.loads(body_unicode)
                message = body_json["rawData"]
                stats = analyzeSingleMail(message)
                queue.pop(analysis_id, None)
                Cache.set("onDemand_analysis_queue", queue)
                return JsonResponse(stats)
            except:
                queue.pop(analysis_id, None)
                Cache.set("onDemand_analysis_queue", queue)
                raise
