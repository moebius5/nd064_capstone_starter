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
    channel = grpc.insecure_channel("localhost:9556")
    stub = demo_pb2_grpc.AdService2Stub(channel)

    # TODO
    # form a request with the required input
    category = ""
    adrequest = demo_pb2.AdRequest(
        context_keys = [category]
    )

    # TODO
    # make a call to server and return a response
    response = stub.GetAds(adrequest)
    logger.info("AdRequest with category=" + category + " was sent")

    # Uncomment to log the response from the Server
    logger.info(response)
    print(response)