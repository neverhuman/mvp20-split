"""One exact dense Dot collection per owned attempt namespace; no aliases/deletion."""

import re

from ..validation import require
from .transport import QdrantError


def path(namespace):
    require(type(namespace) is str and re.fullmatch(r"amphora_[0-9a-f]{64}", namespace), "qdrant_namespace")
    return "/collections/" + namespace


def result(response):
    if type(response) is not dict or response.get("status") != "ok" or "result" not in response:
        raise QdrantError("qdrant_result_shape")
    return response["result"]


def dimensions(info):
    try:
        config = info["config"]
        params = config["params"]
        vectors = params["vectors"]
        require(type(vectors) is dict and vectors.get("distance") == "Dot", "qdrant_collection_space")
        require(
            vectors.get("datatype") in (None, "float32") and vectors.get("multivector_config") is None,
            "qdrant_collection_space",
        )
        require(
            config.get("quantization_config") is None
            and vectors.get("quantization_config") is None
            and not params.get("sparse_vectors"),
            "qdrant_collection_space",
        )
        size = vectors["size"]
        require(type(size) is int and 1 <= size <= 4096, "qdrant_collection_dimensions")
        return size
    except (KeyError, TypeError) as error:
        raise QdrantError("qdrant_collection_shape") from error


class Collections:
    def __init__(self, transport):
        self.transport = transport

    def read(self, namespace, *, missing=False):
        response = self.transport.request("GET", path(namespace), allow_missing=missing)
        return None if response is None else result(response)

    def ensure(self, namespace, size):
        info = self.read(namespace, missing=True)
        if info is None:
            try:
                created = result(
                    self.transport.request(
                        "PUT",
                        path(namespace),
                        {
                            "vectors": {"size": size, "distance": "Dot", "datatype": "float32"},
                            "shard_number": 1,
                            "replication_factor": 1,
                            "write_consistency_factor": 1,
                        },
                    )
                )
                require(created is True, "qdrant_collection_creation")
            except QdrantError as error:
                if str(error) not in {"qdrant_http_400", "qdrant_http_409"}:
                    raise
                # A concurrent identical creator may have won. Actual config still must match.
            info = self.read(namespace)
        require(dimensions(info) == size, "qdrant_collection_dimensions")
        return info
