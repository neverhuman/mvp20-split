#!/usr/bin/env bash
set -euo pipefail

readonly rdkit_commit="42fe8c952589bb750e27ea7f259a50b36576bfa5"
readonly rdkit_version="2026.03.2"
readonly boost_version="1.89.0"
readonly boost_archive="boost_1_89_0.tar.bz2"
readonly boost_sha256="85a33fa22621b4f314f8e85e1a5e2a9363d22e4f4992925d4bb3bc631b5a0c7a"
readonly install_prefix="${1:?usage: build-rdkit-2026.03.2.sh INSTALL_PREFIX}"
readonly parallel_jobs="${RDKIT_BUILD_JOBS:-2}"

task_temp_dir="$(mktemp -d)"
readonly task_temp_dir
trap 'rm -rf -- "${task_temp_dir}"' EXIT

curl --fail --silent --show-error --location --proto '=https' \
  "https://archives.boost.io/release/${boost_version}/source/${boost_archive}" \
  --output "${task_temp_dir}/${boost_archive}"
observed_boost_sha256="$(sha256sum "${task_temp_dir}/${boost_archive}" | cut -d' ' -f1)"
if [[ "${observed_boost_sha256}" != "${boost_sha256}" ]]; then
  echo "Boost source identity mismatch" >&2
  exit 1
fi
tar -xjf "${task_temp_dir}/${boost_archive}" -C "${task_temp_dir}"
(
  cd "${task_temp_dir}/boost_1_89_0"
  ./bootstrap.sh --prefix="${install_prefix}"
  ./b2 \
    --prefix="${install_prefix}" \
    --with-iostreams \
    --with-serialization \
    address-model=64 \
    link=static \
    runtime-link=static \
    variant=release \
    install \
    -j"${parallel_jobs}"
)

git clone --filter=blob:none --no-checkout https://github.com/rdkit/rdkit.git \
  "${task_temp_dir}/src"
git -C "${task_temp_dir}/src" checkout --detach "${rdkit_commit}"

observed_commit="$(git -C "${task_temp_dir}/src" rev-parse HEAD)"
if [[ "${observed_commit}" != "${rdkit_commit}" ]]; then
  echo "RDKit source identity mismatch" >&2
  exit 1
fi

cmake -S "${task_temp_dir}/src" -B "${task_temp_dir}/build" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_STANDARD=20 \
  -DCMAKE_INSTALL_PREFIX="${install_prefix}" \
  -DCMAKE_INSTALL_LIBDIR=lib \
  -DCMAKE_PREFIX_PATH="${install_prefix}" \
  -DRDK_BUILD_PYTHON_WRAPPERS=OFF \
  -DBUILD_TESTING=OFF \
  -DRDK_BUILD_CPP_TESTS=OFF \
  -DRDK_INSTALL_STATIC_LIBS=OFF \
  -DRDK_BUILD_INCHI_SUPPORT=OFF \
  -DRDK_BUILD_AVALON_SUPPORT=OFF \
  -DRDK_BUILD_COORDGEN_SUPPORT=OFF \
  -DRDK_BUILD_MAEPARSER_SUPPORT=OFF \
  -DRDK_BUILD_CHEMDRAW_SUPPORT=OFF \
  -DRDK_BUILD_DESCRIPTORS3D=OFF \
  -DRDK_BUILD_FREETYPE_SUPPORT=OFF \
  -DRDK_BUILD_MOLINTERCHANGE_SUPPORT=OFF \
  -DRDK_BUILD_PUBCHEMSHAPE_SUPPORT=OFF \
  -DRDK_BUILD_SLN_SUPPORT=OFF \
  -DRDK_USE_BOOST_IOSTREAMS=OFF \
  -DRDK_USE_BOOST_SERIALIZATION=OFF \
  -DRDK_USE_BOOST_STACKTRACE=OFF \
  -DRDK_USE_URF=OFF \
  -DRDK_INSTALL_COMIC_FONTS=OFF \
  -DRDK_INSTALL_INTREE=OFF
cmake --build "${task_temp_dir}/build" --parallel "${parallel_jobs}"
cmake --install "${task_temp_dir}/build"

version_config="${install_prefix}/lib/cmake/rdkit/rdkit-config-version.cmake"
if [[ ! -f "${version_config}" ]] || \
  ! grep -q "set(PACKAGE_VERSION \"${rdkit_version}\")" "${version_config}"; then
  echo "installed RDKit did not report ${rdkit_version}" >&2
  exit 1
fi

echo "RDKit ${rdkit_version} installed from ${rdkit_commit} with Boost ${boost_version} (${boost_sha256})"
echo "export RDKIT_INCLUDE_DIR=${install_prefix}/include/rdkit"
echo "export RDKIT_LIB_DIR=${install_prefix}/lib"
echo "export BOOST_INCLUDE_DIR=${install_prefix}/include"
