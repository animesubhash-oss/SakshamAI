"""Thin bridges between the SakshamAI interface and the existing backend.

Every module here forwards to backend code that already exists; none of them
contain study logic, prompts or model configuration of their own.
"""

from .bootstrap import BackendError, backend_status, prepare_backend

__all__ = ["BackendError", "backend_status", "prepare_backend"]
