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
        all_products = getProductsMap()
        products = getProductsByCategory(all_products, request.context_keys)
        if not products:
            products = getRandomProduct(all_products)
        if not products:
            return demo_pb2.Empty()
        result = demo_pb2.AdResponse()
        for product in products:
            result.ads.append(
                demo_pb2.Ad(
                    redirect_url = "/product/" + product.id,
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


def getProductsMap():
    """
    Makes a call to the productcatalogservice for a list of all products
    """
    #channel = grpc.insecure_channel("localhost:30550")
    channel = grpc.insecure_channel("productcatalogservice:3550")
    stub = demo_pb2_grpc.ProductCatalogServiceStub(channel)
    try:
        response = stub.ListProducts(demo_pb2.Empty())
        products = response.products
    except grpc.RpcError as rpc_error:
        if rpc_error.code() == grpc.StatusCode.UNAVAILABLE:
            products = []
            logger.warning("productcatalogservice service is unavailable")
        else:
            products = []
            logger.warning(f"Received gRPC error: code={rpc_error.code()} message={rpc_error.details()}")
    return products


def getProductsByCategory(all_products, search_categories_list):
    """
    Returns the list of products by specified search category
    """
    search_products = []
    for product in all_products:
        for search_category in search_categories_list:
            for category in product.categories:
                if category == search_category:
                    search_products.append(product)
    return search_products


def getRandomProduct(all_products):
    """
    Returns randomly selected product from all products
    """
    if not all_products:
        return []
    return [all_products[random.randrange(len(all_products))]]


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
        health_pb2.DESCRIPTOR.services_by_name['Health'].full_name,
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


