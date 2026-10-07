import os
from pathlib import Path

import pytest
from amphora_deployment.tool_access import TLSIdentity


@pytest.fixture
def identity(tmp_path):
    openssl = Path("C:/Program Files/Git/usr/bin/openssl.exe")
    if os.name != "nt" or not openssl.is_file():
        pytest.skip("Selected Windows/OpenSSL profile required")
    return TLSIdentity.create(tmp_path / "tls", "test-deployment", openssl)
