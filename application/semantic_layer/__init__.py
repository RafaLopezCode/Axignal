"""Semantic judgment layer (spec 062, ADR-0090).

Python compiles world-level state and owns policy; a fast System One evaluator (Jev
today) answers many narrow typed questions per call; a reasoning model (Luna today)
is consulted only when a judgment that matters stays uncertain. Every answer is a
replaceable, non-authoritative judgment: never evidence admission, never truth.
"""
