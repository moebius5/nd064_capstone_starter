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
from jaeger_client import Config
from jaeger_client.metrics.prometheus import PrometheusMetricsFactory

from logger import getJSONLogger
logger = getJSONLogger('adservice-v2-server')


def init_tracer(service):
    config = Config(
        config={
            "sampler": {"type": "const", "param": 1},
            "logging": True,
            "reporter_batch_size": 1,
        },
        service_name=service,
        validate=True,
        metrics_factory=PrometheusMetricsFactory(service_name_label=service),
    )
    # this call also sets opentracing.tracer
    return config.initialize_tracer()

tracer = init_tracer("Ad-V2-service")


class AdServiceV2(demo_pb2_grpc.AdService2Servicer):
    # TODO:
    # Implement the Ad service business logic
    def GetAds(self, request, context):
        logger.info("Got request for getting Ads")
        with tracer.start_span('GetAdsSpan') as span1:
            span1.set_tag('context_keys', str(request.context_keys))
            span1.log_kv({"event:": "serving GetAds request", "context_keys": str(request.context_keys)})
            with tracer.start_span('getProductsMapSpan', child_of=span1) as span2:
                span2.log_kv({"event:": "getting the list of all products"})
                all_products = getProductsMap()
            with tracer.start_span('getProductsByCategorySpan', child_of=span1) as span3:
                span3.log_kv({"event:": "fetching all products with categories: " + str(request.context_keys)})
                products = getProductsByCategory(all_products, request.context_keys)
            if not products:
                with tracer.start_span('getRandomProductSpan', child_of=span1) as span4:
                    span4.log_kv({"event:": "fetching random product"})
                    products = getRandomProduct(all_products)
            if not products:
                logger.info("No products received, return empty response")
                span1.set_tag('response', 'Empty')
                span1.log_kv({"event:": "no products received, return empty response"})
                return demo_pb2.Empty()
            result = demo_pb2.AdResponse()
            for product in products:
                result.ads.append(
                    demo_pb2.Ad(
                        redirect_url = "/product/" + product.id,
                        text = "AdV2 - Items with 25% discount!"
                    )
                )
            span1.set_tag('response', 'Success')
            span1.log_kv({"event:": "returning the resulting Ads list"})
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


