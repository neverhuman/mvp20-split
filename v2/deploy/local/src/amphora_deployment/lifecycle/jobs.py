"""Noninherited Windows jobs: teardown uses handles, never stored process IDs."""

import ctypes
from ctypes import wintypes
import os

from ..profile import ProfileError, require


class BasicLimits(ctypes.Structure):
    _fields_ = [("process_time", ctypes.c_longlong), ("job_time", ctypes.c_longlong),
                ("flags", wintypes.DWORD), ("minimum", ctypes.c_size_t), ("maximum", ctypes.c_size_t),
                ("active", wintypes.DWORD), ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD), ("scheduling", wintypes.DWORD)]


class ExtendedLimits(ctypes.Structure):
    _fields_ = [("basic", BasicLimits), ("io", ctypes.c_ulonglong * 6),
                ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                ("peak_process", ctypes.c_size_t), ("peak_job", ctypes.c_size_t)]


class ProcessJob:
    def __init__(self):
        require(os.name == "nt", "lifecycle_windows_required")
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        declarations = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (arguments, result) in declarations.items():
            function = getattr(self.api, name)
            function.argtypes, function.restype = arguments, result
        self.handle = self.api.CreateJobObjectW(None, None)
        require(bool(self.handle), "lifecycle_job_creation")
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise ProfileError("lifecycle_job_configuration")

    def attach(self, process):
        require(bool(self.handle) and process.poll() is None, "lifecycle_job_unavailable")
        # Popen's owned HANDLE binds the exact process instance, independent of PID reuse.
        require(bool(self.api.AssignProcessToJobObject(self.handle, int(process._handle))), "lifecycle_job_assignment")

    def close(self):
        if self.handle:
            handle, self.handle = self.handle, None
            require(bool(self.api.CloseHandle(handle)), "lifecycle_job_close")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
