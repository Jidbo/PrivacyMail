from identity.rating.calculate import (
    scaleToRating,
    countToRating,
)
from django.db.models import Q

from identity.models import ServiceThirdPartyEmbeds, Service


def highNumber(embeds, service, rMin, rMax):
    return countToRating(
        embeds.filter(
            ((Q(embed_type=ServiceThirdPartyEmbeds.ONVIEW) &
                (Q(thirdparty__sector="tracker") | Q(thirdparty__sector="unkown"))) |
                (Q(embed_type=ServiceThirdPartyEmbeds.ONCLICK) &
                    (Q(thirdparty__sector="tracker") | Q(thirdparty__sector="unkown"))) &
                Q(thirdparty__name=service.name))
        ).count(),
        rMin,
        rMax,
    )


def trackers(embeds, service, rMin, rMax):
    tracker_embeds = embeds.filter(
            ((Q(embed_type=ServiceThirdPartyEmbeds.ONVIEW) &
                (Q(thirdparty__sector="tracker") | Q(thirdparty__sector="unkown"))) |
                (Q(embed_type=ServiceThirdPartyEmbeds.ONCLICK) &
                    (Q(thirdparty__sector="tracker") | Q(thirdparty__sector="unkown"))) &
                Q(thirdparty__name=service.name))
        ).distinct(),
    big = 0
    small = 0

    for tracker_embed in tracker_embeds[0]:
        if Service.objects.filter(thirdparties=tracker_embed.thirdparty).count() > 10:
            big = big+1
        else :
            small = small+1

    return countToRating(
        big * 2 + small,
        rMin,
        rMax,
    )


def calculateTrackingServices(embeds, service, weights, rMin, rMax):
    return {
        "weight": weights["bigTrackers"],
        "rating": scaleToRating(
            trackers(embeds, service, rMin["smallTrackers"], rMax["bigTrackers"]),
            rMax["bigTrackers"],
        ),
    }
