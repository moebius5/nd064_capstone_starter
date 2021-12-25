#!/usr/bin/python

import sys
import grpc
import demo_pb2
import demo_pb2_grpc

from logger import getJSONLogger
logger = getJSONLogger('adservice-v2-server')

if __name__ == "__main__":

    # TODO
    # set up server stub
    # ensure the service is listening to port 9556
    channel = grpc.insecure_channel("localhost:30550")
    stub = demo_pb2_grpc.ProductCatalogServiceStub(channel)

    # TODO
    # make a call to server and return a response
    response = stub.ListProducts(demo_pb2.Empty())

    # Uncomment to log the response from the Server
    logger.info(response)
    print(response.products)