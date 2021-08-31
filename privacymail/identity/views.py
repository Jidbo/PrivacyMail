from django.shortcuts import render
from django.views.generic import View
from identity.util import validate_domain, convertForJsonResponse
from identity.models import Identity, Service, ServiceThirdPartyEmbeds
from django.http import HttpResponseNotFound
from identity.filters import ServiceFilter
from identity.tables import ServiceTable
from mailfetcher.models import Mail, Thirdparty
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from django.shortcuts import redirect
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from django.conf import settings
from mailfetcher import analyser_cron
from mailfetcher.analyser_cron import create_service_cache
import logging
import time
import json
from random import shuffle
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Get named logger
logger = logging.getLogger(__name__)


class StatisticView(View):
    def get_global_stats(self):
        return {
            "email_count": Mail.objects.count(),
            # TODO Ensure that service has at least 1 confirmed ident
            "service_count": Service.objects.count(),
            # TODO Model will be renamed on merge
            "tracker_count": Thirdparty.objects.count(),
        }

    def get(self, request, *args, **kwargs):
        # Get the last approved services
        return JsonResponse({"global_stats": self.get_global_stats()})


class IdentityView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(IdentityView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            # Get service from database
            body_unicode = request.body.decode("utf-8")
            body = json.loads(body_unicode)
            domain = body["domain"]
        except KeyError:
            # No service kwarg is set, warn
            logger.warn(
                "ServiceMetaView.post: Malformed POST request received",
                extra={"request": request},
            )
            # TODO: Add code to display a warning on homepage
            return JsonResponse(convertForJsonResponse({"success": False}))
        try:
            # Format domain. Will also ensure that the domain is valid, and return None on invalid domains
            domain = validate_domain(domain)
        except KeyError:
            # Someone is messing with us. Log this.
            logger.warning(
                "IdentityView.post: Malformed POST request received",
                extra={"request": request},
            )
            # Send them back to the homepage with a slap on the wrist
            # TODO: Add code to display a warning on homepage
            return JsonResponse(convertForJsonResponse({"success": False}))
        # Check if people are messing with us
        except AssertionError:
            # Someone may be messing with us. Save it, just in case.
            logger.info(
                "IdentityView.post: Invalid URL passed",
                extra={"request": request, "domain": domain},
            )
            # Send them back to the homepage with a slap on the wrist
            # TODO: Add code to display a warning on homepage
            return JsonResponse(convertForJsonResponse({"success": False}))

        # Get or create service
        service, created = Service.get_or_create(url=domain, name=domain)
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

        # Display the result to the user
        return JsonResponse(convertForJsonResponse(ident))


class ServiceView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(ServiceView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)

        try:
            # Get service from database
            service = Service.objects.get(name=body["serviceID"])
        except KeyError:
            # No service kwarg is set, warn
            logger.warn(
                "ServiceMetaView.post: Malformed POST request received",
                extra={"request": request},
            )
            # TODO: Add code to display a warning on homepage
            return JsonResponse(convertForJsonResponse({"success": False}))
        except ObjectDoesNotExist:
            logger.warn(
                "ServiceMetaView.post: POST request for non-existing service",
                extra={"request": request},
            )
            return JsonResponse(convertForJsonResponse({"success": False}))

        # Form is valid
        sector = body["sector"]
        country = body["country_of_origin"]

        if sector != "" and country != "":
            service.country_of_origin = country
            service.sector = sector
            service.save()
            return JsonResponse(convertForJsonResponse({"success": True}))

        else:
            return JsonResponse(convertForJsonResponse({"success": False}))

    def get(self, request, *args, **kwargs):
        # Check if the kwarg is even set
        try:
            sid = kwargs["service"]
        except KeyError:
            try:
                sid = self.parseUrlToId(request.GET.get("url"))
            except:
                return HttpResponseNotFound("newsletter not found")

        try:
            service = Service.objects.get(id=sid)
        except ObjectDoesNotExist:
            logger.info(
                "ServiceView.get: Invalid service requested",
                extra={"request": request, "service_id": sid},
            )
            # TODO: Add code to display a warning on homepage
            return redirect("Home")
        return JsonResponse(
            convertForJsonResponse(self.render_service(request, service))
        )

    @staticmethod
    def parseUrlToId(url):
        domain = validate_domain(url)
        service = Service.objects.get(url=domain)
        return service.id

    @staticmethod
    def render_service(request, service, form=None):

        site_params = ServiceView.get_service_site_params(service)
        if site_params is None:
            logger.warn(
                "ServiceView.render_service: Cache miss",
                extra={"request": request, "service_id": service.id},
            )
            # Display a warning that the cache isn't up to date
            # TODO We probably also want to mark the service as dirty to ensure its generated, just in case
            # stuff went wrong somewhere
            return render(
                request,
                "identity/service.html",
                {"error": "cache miss", "service": service},
            )

        # Render the site
        if form is None:
            # site_params['form'] = forms.ServiceMetadataForm(instance=service)
            pass
            # TODO uncomment
        else:
            site_params["form"] = form
        site_params["service"] = service
        site_params["checks"] = []
        site_params["reliability"] = {
            "mailOpen": "reliable",
            "linkClicked": "unreliable",
            "abTesting": "unreliable",
            "spam": "reliable",
            "personalisedLinks": "reliable",
        }
        # Run checks
        # for check in checks.SERVICE_CHECKS:
        #    site_params['checks'].append(check(site_params))
        # TODO uncomment

        return site_params

    @staticmethod
    def get_service_site_params(service, force_makecache=False):
        start_time = time.time()
        if force_makecache:
            analyser_cron.create_service_cache(service, force=True)
        site_params = cache.get(service.derive_service_cache_path())
        if site_params is None:
            return None

        # All identities of the service
        identities = Identity.objects.filter(service=service)
        emails = Mail.objects.filter(
            identity__in=identities, identity__approved=True
        ).distinct()
        service_3p_conns = ServiceThirdPartyEmbeds.objects.filter(service=service)
        third_party_conns_setting_cookies = service_3p_conns.filter(sets_cookie=True)
        third_parties = service.thirdparties.distinct()

        site_params["service"] = service
        # site_params["num_different_idents"] = identities.count()
        site_params["num_different_idents"] = identities.filter(approved=True).count()
        site_params["count_mails"] = emails.count()
        # site_params['unconfirmed_idents'] = identities.filter(approved=False)
        site_params["sets_cookies"] = third_party_conns_setting_cookies.exists()
        site_params["num_different_thirdparties"] = third_parties.count()
        site_params["leaks_address"] = service_3p_conns.filter(
            leaks_address=True
        ).exists()

        end_time = time.time()
        print("Get service_site_params took: {}s".format(end_time - start_time))
        return site_params


class ServiceListView(SingleTableMixin, FilterView):
    model = Service
    table_class = ServiceTable
    template_name = "service_filter.html"
    paginate_by = 25
    filterset_class = ServiceFilter


class EmbedView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(EmbedView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)

        try:
            # Get service from database
            embed = Thirdparty.objects.get(name=body["embedID"])
        except KeyError:
            # No embed kwarg is set, warn
            logger.warn(
                "EmbedMetaView.post: Malformed POST request received",
                extra={"request": request},
            )
            # TODO: Add code to display a warning on homepage
            return JsonResponse(convertForJsonResponse({"success": False}))
        except ObjectDoesNotExist:
            logger.warn(
                "EmbedMetaView.post: POST request for non-existing Thirdparty",
                extra={"request": request},
            )
            return JsonResponse(convertForJsonResponse({"success": False}))

        # Form is valid
        sector = body["sector"]
        country = body["country_of_origin"]

        if sector != "" and country != "":
            embed.country_of_origin = country
            embed.sector = sector
            embed.save()
            return JsonResponse(convertForJsonResponse({"success": True}))

        else:
            return JsonResponse(convertForJsonResponse({"success": False}))

    def get(self, request, *args, **kwargs):
        # Check if the kwarg is even set
        try:
            sid = kwargs["embed"]
        except KeyError:
            try:
                sid = self.parseUrlToId(request.GET.get("url"))
            except:
                return HttpResponseNotFound("embed not found")
        try:
            embed = Thirdparty.objects.get(id=sid)
        except ObjectDoesNotExist:
            logger.info(
                "EmbedView.get: Invalid service requested",
                extra={"request": request, "service_id": sid},
            )
            # TODO: Add code to display a warning on homepage
            return redirect("Home")

        return JsonResponse(convertForJsonResponse(self.render_embed(request, embed)))

    @staticmethod
    def render_embed(request, embed, form=None):

        site_params = EmbedView.get_embed_site_params(embed)

        # site_params["checks"] = []
        # Add any checks that should be run on embeds
        # for check in checks.EMBED_CHECKS:
        #     site_params["checks"].append(check(site_params))

        # Add the object itself
        return site_params

    @staticmethod
    def get_embed_site_params(embed):
        site_params = cache.get(embed.derive_thirdparty_cache_path())

        if site_params is None:
            return None

        # TODO Add additional uncached metadata here
        site_params["country"] = embed.get_country().code
        site_params["sector"] = embed.get_sector()

        site_params["reliability"] = {
            "mailOpen": "reliable",
            "linkClicked": "unreliable",
            "personalisedLinks": "reliable",
        }

        return site_params

    @staticmethod
    def parseUrlToId(url):
        domain = validate_domain(url)
        print("domain" + domain)
        service = Thirdparty.objects.get(name=domain)
        return service.id
