"""Compatibility shim: implementation lives in `northgard.search`."""

from northgard.search.beam_search import BeamResult, beam_search

__all__ = ["BeamResult", "beam_search"]
