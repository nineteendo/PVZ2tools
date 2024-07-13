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
          align_items=False,    # True -> override indent
          allow=(),             # comments, duplicate_keys, nan, trailing_commas
          ensure_ascii=False,
          indent=None,
          item_separator=', ',  # indent not None -> strip trailing whitespace
          key_separator=': ',
          sort_keys=False,
          ): ...

def loads(data,
          *,
          allow=(),  # comments, duplicate_keys, nan, trailing_commas
          ): ...
```