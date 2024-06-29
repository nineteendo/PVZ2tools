# Python Vs. Zombies 2 (PyVZ2)

TODO:

```py
def rton_decode(fp1,
                fp2,
                *,
                # RTON options
                strict=False,

                # JSON options
                align_items=False,          # True -> override indent
                allow_duplicate_keys=True,  # False -> Python
                allow_nan=True,
                ensure_ascii=False,
                indent='\t',                # None -> no indent
                item_separator=', ',        # indent not None -> strip trailing whitespace
                key_separator=': ',
                sort_keys=False,            # True -> Python
                ) -> None: ...

def rton_encode(fp1,
                fp2,
                *,
                # JSON options
                strict=None,                # False -> C
                ) -> None: ...
```