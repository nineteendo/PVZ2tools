# Python Vs. Zombies 2 (PyVZ2)

## TODO

```python
# rton.py
def dumps(obj,
          *,
          cache_strings=True,
          ): ...

def loads(data,
          *,
          strict=False,
          ): ...
```

```python
# jsonc.py
def dumps(obj,
          *,
          align_items=False,    # True -> override indent
          allow_nan=True,
          ensure_ascii=False,
          indent='\t',          # None -> no indent
          item_separator=', ',  # indent not None -> strip trailing whitespace
          key_separator=': ',
          sort_keys=False,
          ): ...

def loads(data,
          *,
          allow_comments=True,
          allow_nan=True,
          allow_trailing_comma=True,
          ): ...
```