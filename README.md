# Python Vs. Zombies 2 (PyVZ2)

[![pytest](https://github.com/nineteendo/pyvz2/actions/workflows/pytest.yml/badge.svg)](https://github.com/nineteendo/pyvz2/actions/workflows/pytest.yml)

## TODO

```python
# rtonyx/__init__.py
def dumps(obj,
          *,
          cache_strings=False,
          sort_keys=False,
          version=2,  # 1 -> latin_1
          ): ...

def loads(data,
          *,
          strict=True,
          version=2,  # 1 -> latin_1
          ): ...
```
