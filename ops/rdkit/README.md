# Pinned RDKit C++ build

This environment builds only RDKit `2026.03.2` at commit
`42fe8c952589bb750e27ea7f259a50b36576bfa5`. The source archive is locked to
SHA-256 `9bea418c32b553920dc3491b282bbfc47e10728ad20ea874ca47c38cc1b0818b`.

Build the image with:

```text
docker build --network=default --tag amphora-rdkit:2026.03.2 ops/rdkit
```

Copy `/opt/amphora-rdkit` into a content-addressed external toolchain prefix,
record the image digest and all files emitted there, and set
`RDKIT_INCLUDE_DIR`, `RDKIT_LIB_DIR`, `BOOST_INCLUDE_DIR`, and
`LD_LIBRARY_PATH` from that prefix. The compound campaign refuses an absent,
wrong-version, or hash-mismatched runtime. The image does not make the backend
authorized: a signed host evidence grant remains mandatory.

