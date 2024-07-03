# Python Vs. Zombies 2 (PyVZ2)

## TODO

```python
# rton.py
def dumps(obj,
          *,
          cache_strings=False,
          ): ...

def loads(data,
          *,
          strict=True,
          ): ...
```

```python
# jsonc.py
def dumps(obj,
          *,
          allow_nan=False,
          ensure_ascii=False,
          indent=None,
          item_separator=', ',  # indent not None -> strip trailing whitespace
          key_separator=': ',
          sort_keys=False,
          ): ...

def loads(data,
          *,
          allow_comments=False,
          allow_nan=False,
          allow_trailing_comma=False,
          ): ...
```