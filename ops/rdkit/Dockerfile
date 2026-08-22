FROM ubuntu:24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG RDKIT_VERSION=2026.03.2
ARG RDKIT_TAG=Release_2026_03_2
ARG RDKIT_COMMIT=42fe8c952589bb750e27ea7f259a50b36576bfa5
ARG RDKIT_SOURCE_SHA256=9bea418c32b553920dc3491b282bbfc47e10728ad20ea874ca47c38cc1b0818b

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates cmake curl g++ git libboost-all-dev libeigen3-dev \
       libsqlite3-dev make ninja-build pkg-config zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN curl --fail --location --retry 3 \
      --output rdkit.tar.gz \
      "https://github.com/rdkit/rdkit/archive/refs/tags/${RDKIT_TAG}.tar.gz" \
    && echo "${RDKIT_SOURCE_SHA256}  rdkit.tar.gz" | sha256sum --check - \
    && tar --extract --gzip --file rdkit.tar.gz --strip-components=1 --directory /build

RUN cmake -S /build -B /build/out -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_INSTALL_PREFIX=/opt/amphora-rdkit \
      -DRDK_BUILD_CPP_TESTS=OFF \
      -DRDK_BUILD_PYTHON_WRAPPERS=OFF \
      -DRDK_BUILD_INCHI_SUPPORT=ON \
      -DRDK_BUILD_AVALON_SUPPORT=OFF \
      -DRDK_INSTALL_INTREE=OFF \
    && cmake --build /build/out --parallel 2 \
    && cmake --install /build/out

ENV RDKIT_INCLUDE_DIR=/opt/amphora-rdkit/include/rdkit
ENV RDKIT_LIB_DIR=/opt/amphora-rdkit/lib
ENV BOOST_INCLUDE_DIR=/usr/include
ENV LD_LIBRARY_PATH=/opt/amphora-rdkit/lib

RUN test -f /opt/amphora-rdkit/lib/libRDKitGraphMol.so \
    && find /opt/amphora-rdkit/lib -maxdepth 1 -type f -name 'libRDKit*.so*' \
       -print0 | sort -z | xargs -0 sha256sum > /opt/amphora-rdkit/RDKIT-LIBRARY-SHA256SUMS \
    && c++ --version > /opt/amphora-rdkit/compiler-version.txt \
    && cmake --version > /opt/amphora-rdkit/cmake-version.txt \
    && printf '%s\n' \
       "rdkit_version=${RDKIT_VERSION}" \
       "rdkit_tag=${RDKIT_TAG}" \
       "rdkit_commit=${RDKIT_COMMIT}" \
       "source_sha256=${RDKIT_SOURCE_SHA256}" \
       "cmake_build_type=Release" \
       "python_wrappers=OFF" \
       "cpp_tests=OFF" \
       "inchi_support=ON" \
       > /opt/amphora-rdkit/build-flags.txt

