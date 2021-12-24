#!/usr/bin/python

import os
import random
import time
import traceback
from concurrent import futures

import grpc
import demo_pb2
import demo_pb2_grpc
from grpc_health.v1 import health_pb2
from grpc_health.v1 import health_pb2_grpc
from grpc_reflection.v1alpha import reflection

from logger import getJSONLogger
logger = getJSONLogger('adservice-v2-server')


class AdServiceV2(demo_pb2_grpc.AdService2Servicer):
    # TODO:
    # Implement the Ad service business logic
    def GetAds(self, request, context):
        logger.info("Got request for getting Ads")
        allAds = getAdsMap()
        ads = getAdsByCategory(allAds, request.context_keys)
        if not ads:
            ads = getRandomAd(allAds)

        # reformat ads dictionary to protobuffer ads objects and return the final result
        result = demo_pb2.AdResponse()
        for ad in ads:
            result.ads.append(
                demo_pb2.Ad(
                    redirect_url = "/product/" + ad["id"],
                    text = "AdV2 - Items with 25% discount!"
                )
            )
        return result

    # Uncomment to enable the HealthChecks for the Ad service
    # Note: These are needed for the liveness and readiness probes
    def Check(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.SERVING)

    def Watch(self, request, context):
        return health_pb2.HealthCheckResponse(
            status=health_pb2.HealthCheckResponse.UNIMPLEMENTED)


def getAdsMap():
    adsMap = [
        {
            "id": "OLJCESPC7Z",
            "name": "Vintage Typewriter",
            "description": "This typewriter looks good in your living room.",
            "picture": "/static/img/products/typewriter.jpg",
            "priceUsd": {
                "currencyCode": "USD",
                "units": 67,
                "nanos": 990000000
            },
            "categories": ["vintage"]
        },
        {
            "id": "66VCHSJNUP",
            "name": "Vintage Camera Lens",
            "description": "You won't have a camera to use it and it probably doesn't work anyway.",
            "picture": "/static/img/products/camera-lens.jpg",
            "priceUsd": {
                "currencyCode": "USD",
                "units": 12,
                "nanos": 490000000
            },
            "categories": ["photography", "vintage"]
        },
        {
            "id": "1YMWWN1N4O",
            "name": "Home Barista Kit",
            "description": "Always wanted to brew coffee with Chemex and Aeropress at home?",
            "picture": "/static/img/products/barista-kit.jpg",
            "priceUsd": {
                "currencyCode": "USD",
                "units": 124
            },
            "categories": ["cookware"]
        }
    ]
    return adsMap


def getAdsByCategory(adsMap, searchCategoriesList):
    """
    Returns the list of ads by specified search category
    """
    ads = []
    for ad in adsMap:
        for searchCategory in searchCategoriesList:
            for category in ad['categories']:
                if category == searchCategory:
                    ads.append(ad)
    return ads


def getRandomAd(adsMap):
    """
    Returns randomly selected Ad from all Ads
    """
    ads = []
    ads.append(adsMap[random.randrange(len(adsMap))])
    return ads

if __name__ == "__main__":
    logger.info("initializing adservice-v2")

    # TODO:
    # create gRPC server, add the Ad-v2 service and start it
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    demo_pb2_grpc.add_AdService2Servicer_to_server(AdServiceV2(), server)

    # Uncomment to add the HealthChecks to the gRPC server to the Ad-v2 service
    health_pb2_grpc.add_HealthServicer_to_server(AdServiceV2(), server)

    # enabling reflection service
    SERVICE_NAMES = (
        demo_pb2.DESCRIPTOR.services_by_name['AdService2'].full_name,
        reflection.SERVICE_NAME,
    )
    reflection.enable_server_reflection(SERVICE_NAMES, server)

    logger.info("Server starting on port 9556...")
    server.add_insecure_port("[::]:9556")
    server.start()
    # Keep thread alive
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


