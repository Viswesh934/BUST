"""BUST Backend Package."""
try:
    import neatlogs
    if not hasattr(neatlogs, "span"):
        def _noop_span(*args, **kwargs):
            def _decorator(fn):
                return fn
            return _decorator
        neatlogs.span = _noop_span

    if not hasattr(neatlogs, "wrap"):
        def _noop_wrap(client, *args, **kwargs):
            return client
        neatlogs.wrap = _noop_wrap
except Exception:
    pass
