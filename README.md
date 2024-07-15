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
# jsonyx.py
def dumps(obj,
          *,
          allow=(),             # nan
          ensure_ascii=False,
          indent=None,
          item_separator=', ',  # indent not None -> strip trailing whitespace
          key_separator=': ',
          ): ...

def loads(data,
          *,
          allow=(),  # comments, duplicate_keys, nan, trailing_comma
          ): ...
```