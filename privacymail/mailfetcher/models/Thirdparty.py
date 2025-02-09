from __future__ import absolute_import

import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django_countries.fields import CountryField
from identity.models import Service
from identity.util import convertForJsonResponse

logger = logging.getLogger(__name__)


class Thirdparty(models.Model):
    TRACKER = "tracker"
    CDN = "cdn"
    ALT_DOMAIN = "altdomain"
    UNKNOWN = "unknown"

    SECTOR_CHOICES = (
        (TRACKER, "Tracking / Advertising"),
        (CDN, "Hosting / Content Distribution"),
        (ALT_DOMAIN, "Alternative Domain of first party"),
        (UNKNOWN, "Unknown"),
    )

    name = models.CharField(max_length=500, null=False, blank=False)
    host = models.CharField(max_length=500, null=False, blank=False, unique=True)
    resultsdirty = models.BooleanField(default=True)

    # Metadata
    # Do not access country_of_origin and sector directly. Instead, use get_country()
    # and get_sector(), as they also take connections to services into account.
    # (If a service is associated with this host, the metadata of the service are
    # used instead of that saved here)
    country_of_origin = CountryField(blank_label="(select country)", blank=True)
    sector = models.CharField(choices=SECTOR_CHOICES, max_length=30, default=UNKNOWN)
    service = models.OneToOneField(Service, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return "({})|{}".format(self.name, self.host)

    def derive_thirdparty_cache_path(self):
        return "frontend.ThirdPartyView.result." + str(self.id) + ".site_params"

    @classmethod
    def create(cls, name, host):
        tp = cls(name=name, host=host)
        try:
            service = Service.objects.get(url=host)
            tp.service = service
        except ObjectDoesNotExist:
            pass
        tp.save()
        return tp

    def set_dirty(self):
        self.resultsdirty = True
        self.save()

    def get_country(self):
        if self.service:
            return self.service.country_of_origin
        else:
            return self.country_of_origin

    def get_sector(self):
        if self.service:
            return self.service.get_sector_display()
        else:
            return self.get_sector_display()

    def toJSON(self):
        return {
            "name": convertForJsonResponse(self.name),
            "host": convertForJsonResponse(self.host),
            "resultsdirty": convertForJsonResponse(self.resultsdirty),
            "country_of_origin": convertForJsonResponse(self.country_of_origin.code),
            "sector": convertForJsonResponse(self.sector),
            "service": convertForJsonResponse(self.service),
        }
