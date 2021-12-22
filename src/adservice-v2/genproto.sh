#!/bin/bash -eu

set -e

# TODO: Add the commands to generate the gRPC files
mkdir -p protobuffers && \
cp ../../pb/demo.proto ./protobuffers