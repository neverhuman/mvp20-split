"""Windows DPAPI current-user protection with noninteractive calls and bounded blobs."""

import ctypes
import os
from ctypes import wintypes

from ..profile import ProfileError, require


class Blob(ctypes.Structure):
    _fields_ = [("size", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def transform(payload, context, *, protect):
    require(os.name == "nt", "credential_platform_unsupported")
    require(type(payload) is bytes and 0 < len(payload) <= (65536 if protect else 131072), "credential_blob_bound")
    require(type(context) is bytes and 0 < len(context) <= 256, "credential_context_bound")
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    function = crypt32.CryptProtectData if protect else crypt32.CryptUnprotectData
    function.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p,
                         ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    function.restype = wintypes.BOOL
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    source = ctypes.create_string_buffer(payload)
    entropy = ctypes.create_string_buffer(context)
    incoming = Blob(len(payload), ctypes.cast(source, ctypes.POINTER(ctypes.c_ubyte)))
    binding = Blob(len(context), ctypes.cast(entropy, ctypes.POINTER(ctypes.c_ubyte)))
    outgoing = Blob()
    try:
        # UI_FORBIDDEN=1, never LOCAL_MACHINE=4. Both optional prompt parameters NULL.
        if not function(ctypes.byref(incoming), None, ctypes.byref(binding), None, None, 1, ctypes.byref(outgoing)):
            raise ProfileError("credential_protection_failed")
        require(0 < outgoing.size <= (131072 if protect else 65536), "credential_result_bound")
        return ctypes.string_at(outgoing.data, outgoing.size)
    finally:
        ctypes.memset(source, 0, len(source))
        if outgoing.data:
            if not protect:
                ctypes.memset(outgoing.data, 0, outgoing.size)
            kernel32.LocalFree(outgoing.data)
