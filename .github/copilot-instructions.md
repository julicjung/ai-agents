You *must* prefer protocol over classes to support structural subtyping. Ignore this if you need runtime type checks.
You *must* prefer match statements over if-elif-else and if-else. if statements without else are fine.
You *must* use type hints everywhere. You *must avoid Dict[str, str]. Use a Protocol or dataclass instead.
You *always must* write docstrings!  