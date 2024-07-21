/* JSON accelerator C extensor: _jsonyx module. */

#include <Python.h>
#include <structmember.h>
#include <stdbool.h> // bool

#ifndef _Py_T_OBJECT
#define _Py_T_OBJECT T_OBJECT
#endif
#ifndef Py_READONLY
#define Py_READONLY READONLY
#endif
#ifndef Py_T_BOOL
#define Py_T_BOOL T_BOOL
#endif

#define _Py_EnterRecursiveCall Py_EnterRecursiveCall
#define _Py_LeaveRecursiveCall Py_LeaveRecursiveCall


typedef struct _PyScannerObject {
    PyObject_HEAD
    PyObject *Decimal;
    int allow_comments;
    int allow_duplicate_keys;
    int allow_missing_commas;
    int allow_nan_and_infinity;
    int allow_trailing_comma;
    int use_decimal;
} PyScannerObject;

typedef struct _PyEncoderObject {
    PyObject_HEAD
    PyObject *Decimal;
    PyObject *encode_decimal;
    PyObject *indent;
    PyObject *key_separator;
    PyObject *item_separator;
    int sort_keys;
    int allow_nan_and_infinity;
    int ensure_ascii;
} PyEncoderObject;

static Py_hash_t duplicatekey_hash(PyUnicodeObject *self) {
    return (Py_hash_t)self;
}

static PyTypeObject PyDuplicateKeyType = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "_jsonyx.DuplicateKey",
    .tp_doc = PyDoc_STR("Duplicate key"),
    .tp_hash = (hashfunc)duplicatekey_hash,
};

/* Forward decls */

static PyObject *
ascii_escape_unicode(PyObject *pystr);
static PyObject *
py_encode_basestring_ascii(PyObject* Py_UNUSED(self), PyObject *pystr);
static PyObject *
scan_once_unicode(PyScannerObject *s, PyObject *memo, PyObject *pyfilename, PyObject *pystr, Py_ssize_t idx, Py_ssize_t *next_idx_ptr);
static PyObject *
scanner_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static void
scanner_dealloc(PyObject *self);
static int
scanner_clear(PyScannerObject *self);
static PyObject *
encoder_new(PyTypeObject *type, PyObject *args, PyObject *kwds);
static void
encoder_dealloc(PyObject *self);
static int
encoder_clear(PyEncoderObject *self);
static int
encoder_listencode_list(PyEncoderObject *s, PyObject *markers, _PyUnicodeWriter *writer, PyObject *seq, PyObject *newline_indent);
static int
encoder_listencode_obj(PyEncoderObject *s, PyObject *markers, _PyUnicodeWriter *writer, PyObject *obj, PyObject *newline_indent);
static int
encoder_listencode_dict(PyEncoderObject *s, PyObject *markers, _PyUnicodeWriter *writer, PyObject *dct, PyObject *newline_indent);
static void
raise_errmsg(const char *msg, PyObject *filename, PyObject *s, Py_ssize_t start, Py_ssize_t end);
static PyObject *
encoder_encode_string(PyEncoderObject *s, PyObject *obj);
static PyObject *
encoder_encode_float(PyEncoderObject *s, PyObject *obj);

#define S_CHAR(c) (c >= ' ' && c <= '~' && c != '\\' && c != '"')
#define IS_WHITESPACE(c) (((c) == ' ') || ((c) == '\t') || ((c) == '\n') || ((c) == '\r'))

static int
_skip_comments(PyScannerObject *s, PyObject *pyfilename, PyObject *pystr, Py_ssize_t *idx_ptr)
{
    const void *str;
    int kind;
    Py_ssize_t len;
    Py_ssize_t idx;
    Py_ssize_t comment_idx;

    str = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);
    len = PyUnicode_GET_LENGTH(pystr);
    idx = *idx_ptr;
    while (1) {
        while (idx < len && IS_WHITESPACE(PyUnicode_READ(kind,str, idx))) {
            idx++;
        }
        comment_idx = idx;
        if (idx + 1 < len && PyUnicode_READ(kind, str, idx) == '/' &&
            PyUnicode_READ(kind, str, idx + 1) == '/')
        {
            idx += 2;
            while (idx < len && PyUnicode_READ(kind,str, idx) != '\n') {
                idx++;
            }
        }
        else if (idx + 1 < len && PyUnicode_READ(kind, str, idx) == '/' &&
                 PyUnicode_READ(kind, str, idx + 1) == '*')
        {
            idx += 2;
            while (1) {
                if (idx + 1 >= len) {
                    if (s->allow_comments) {
                        raise_errmsg("Unterminated comment", pyfilename, pystr, comment_idx, len);
                    }
                    else {
                        raise_errmsg("Comments are not allowed", pyfilename, pystr, comment_idx, len);
                    }
                    return -1;
                }
                if (PyUnicode_READ(kind,str, idx) == '*' &&
                    PyUnicode_READ(kind,str, idx + 1) == '/')
                {
                    break;
                }
                idx++;
            }
            idx += 2;
        }
        else {
            break;
        }
        if (!s->allow_comments) {
            raise_errmsg("Comments are not allowed", pyfilename, pystr, comment_idx, idx);
            return -1;
        }
    }
    *idx_ptr = idx;
    return 0;
}

static Py_ssize_t
ascii_escape_unichar(Py_UCS4 c, unsigned char *output, Py_ssize_t chars)
{
    /* Escape unicode code point c to ASCII escape sequences
    in char *output. output must have at least 12 bytes unused to
    accommodate an escaped surrogate pair "\uXXXX\uXXXX" */
    output[chars++] = '\\';
    switch (c) {
        case '\\': output[chars++] = c; break;
        case '"': output[chars++] = c; break;
        case '\b': output[chars++] = 'b'; break;
        case '\f': output[chars++] = 'f'; break;
        case '\n': output[chars++] = 'n'; break;
        case '\r': output[chars++] = 'r'; break;
        case '\t': output[chars++] = 't'; break;
        default:
            if (c >= 0x10000) {
                /* UTF-16 surrogate pair */
                Py_UCS4 v = Py_UNICODE_HIGH_SURROGATE(c);
                output[chars++] = 'u';
                output[chars++] = Py_hexdigits[(v >> 12) & 0xf];
                output[chars++] = Py_hexdigits[(v >>  8) & 0xf];
                output[chars++] = Py_hexdigits[(v >>  4) & 0xf];
                output[chars++] = Py_hexdigits[(v      ) & 0xf];
                c = Py_UNICODE_LOW_SURROGATE(c);
                output[chars++] = '\\';
            }
            if (0xd800 <= c && c <= 0xdfff) {
                PyErr_Format(PyExc_ValueError,
                             "Surrogate '\\u%x' can not be escaped", c);
                return -1;
            }
            output[chars++] = 'u';
            output[chars++] = Py_hexdigits[(c >> 12) & 0xf];
            output[chars++] = Py_hexdigits[(c >>  8) & 0xf];
            output[chars++] = Py_hexdigits[(c >>  4) & 0xf];
            output[chars++] = Py_hexdigits[(c      ) & 0xf];
    }
    return chars;
}

static PyObject *
ascii_escape_unicode(PyObject *pystr)
{
    /* Take a PyUnicode pystr and return a new ASCII-only escaped PyUnicode */
    Py_ssize_t i;
    Py_ssize_t input_chars;
    Py_ssize_t output_size;
    Py_ssize_t chars;
    PyObject *rval;
    const void *input;
    Py_UCS1 *output;
    int kind;

    input_chars = PyUnicode_GET_LENGTH(pystr);
    input = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);

    /* Compute the output size */
    for (i = 0, output_size = 2; i < input_chars; i++) {
        Py_UCS4 c = PyUnicode_READ(kind, input, i);
        Py_ssize_t d;
        if (S_CHAR(c)) {
            d = 1;
        }
        else {
            switch(c) {
            case '\\': case '"': case '\b': case '\f':
            case '\n': case '\r': case '\t':
                d = 2; break;
            default:
                d = c >= 0x10000 ? 12 : 6;
            }
        }
        if (output_size > PY_SSIZE_T_MAX - d) {
            PyErr_SetString(PyExc_OverflowError, "string is too long to escape");
            return NULL;
        }
        output_size += d;
    }

    rval = PyUnicode_New(output_size, 127);
    if (rval == NULL) {
        return NULL;
    }
    output = PyUnicode_1BYTE_DATA(rval);
    chars = 0;
    output[chars++] = '"';
    for (i = 0; i < input_chars; i++) {
        Py_UCS4 c = PyUnicode_READ(kind, input, i);
        if (S_CHAR(c)) {
            output[chars++] = c;
        }
        else {
            chars = ascii_escape_unichar(c, output, chars);
            if (chars < 0) {
                return NULL;
            }
        }
    }
    output[chars++] = '"';
#ifdef Py_DEBUG
    assert(_PyUnicode_CheckConsistency(rval, 1));
#endif
    return rval;
}

static PyObject *
escape_unicode(PyObject *pystr)
{
    /* Take a PyUnicode pystr and return a new escaped PyUnicode */
    Py_ssize_t i;
    Py_ssize_t input_chars;
    Py_ssize_t output_size;
    Py_ssize_t chars;
    PyObject *rval;
    const void *input;
    int kind;
    Py_UCS4 maxchar;

    maxchar = PyUnicode_MAX_CHAR_VALUE(pystr);
    input_chars = PyUnicode_GET_LENGTH(pystr);
    input = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);

    /* Compute the output size */
    for (i = 0, output_size = 2; i < input_chars; i++) {
        Py_UCS4 c = PyUnicode_READ(kind, input, i);
        Py_ssize_t d;
        switch (c) {
        case '\\': case '"': case '\b': case '\f':
        case '\n': case '\r': case '\t':
            d = 2;
            break;
        default:
            if (c <= 0x1f)
                d = 6;
            else
                d = 1;
        }
        if (output_size > PY_SSIZE_T_MAX - d) {
            PyErr_SetString(PyExc_OverflowError, "string is too long to escape");
            return NULL;
        }
        output_size += d;
    }

    rval = PyUnicode_New(output_size, maxchar);
    if (rval == NULL)
        return NULL;

    kind = PyUnicode_KIND(rval);

#define ENCODE_OUTPUT do { \
        chars = 0; \
        output[chars++] = '"'; \
        for (i = 0; i < input_chars; i++) { \
            Py_UCS4 c = PyUnicode_READ(kind, input, i); \
            switch (c) { \
            case '\\': output[chars++] = '\\'; output[chars++] = c; break; \
            case '"':  output[chars++] = '\\'; output[chars++] = c; break; \
            case '\b': output[chars++] = '\\'; output[chars++] = 'b'; break; \
            case '\f': output[chars++] = '\\'; output[chars++] = 'f'; break; \
            case '\n': output[chars++] = '\\'; output[chars++] = 'n'; break; \
            case '\r': output[chars++] = '\\'; output[chars++] = 'r'; break; \
            case '\t': output[chars++] = '\\'; output[chars++] = 't'; break; \
            default: \
                if (c <= 0x1f) { \
                    output[chars++] = '\\'; \
                    output[chars++] = 'u'; \
                    output[chars++] = '0'; \
                    output[chars++] = '0'; \
                    output[chars++] = Py_hexdigits[(c >> 4) & 0xf]; \
                    output[chars++] = Py_hexdigits[(c     ) & 0xf]; \
                } else { \
                    output[chars++] = c; \
                } \
            } \
        } \
        output[chars++] = '"'; \
    } while (0)

    if (kind == PyUnicode_1BYTE_KIND) {
        Py_UCS1 *output = PyUnicode_1BYTE_DATA(rval);
        ENCODE_OUTPUT;
    } else if (kind == PyUnicode_2BYTE_KIND) {
        Py_UCS2 *output = PyUnicode_2BYTE_DATA(rval);
        ENCODE_OUTPUT;
    } else {
        Py_UCS4 *output = PyUnicode_4BYTE_DATA(rval);
        assert(kind == PyUnicode_4BYTE_KIND);
        ENCODE_OUTPUT;
    }
#undef ENCODE_OUTPUT

#ifdef Py_DEBUG
    assert(_PyUnicode_CheckConsistency(rval, 1));
#endif
    return rval;
}

static void
raise_errmsg(const char *msg, PyObject *filename, PyObject *s, Py_ssize_t start, Py_ssize_t end)
{
    /* Use JSONSyntaxError exception to raise a nice looking SyntaxError subclass */
    PyObject *json = PyImport_ImportModule("jsonyx");
    if (json == NULL) {
        return;
    }
    PyObject *JSONSyntaxError = PyObject_GetAttrString(json, "JSONSyntaxError");
    Py_DECREF(json);
    if (JSONSyntaxError == NULL) {
        return;
    }

    PyObject *exc;
    exc = PyObject_CallFunction(JSONSyntaxError, "zOOnn", msg, filename, s, start, end);
    Py_DECREF(JSONSyntaxError);
    if (exc) {
        PyErr_SetObject(JSONSyntaxError, exc);
        Py_DECREF(exc);
    }
}

static PyObject *
scanstring_unicode(PyObject *pyfilename, PyObject *pystr, Py_ssize_t end, Py_ssize_t *next_end_ptr)
{
    /* Read the JSON string from PyUnicode pystr.
    end is the index of the first character after the quote.
    *next_end_ptr is a return-by-reference index of the character
        after the end quote

    Return value is a new PyUnicode
    */
    PyObject *rval = NULL;
    Py_ssize_t len;
    Py_ssize_t begin = end - 1;
    Py_ssize_t next /* = begin */;
    const void *buf;
    int kind;

    _PyUnicodeWriter writer;
    _PyUnicodeWriter_Init(&writer);
    writer.overallocate = 1;

    len = PyUnicode_GET_LENGTH(pystr);
    buf = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);

    if (end < 0 || len < end) {
        PyErr_SetString(PyExc_ValueError, "end is out of bounds");
        goto bail;
    }
    while (1) {
        /* Find the end of the string or the next escape */
        Py_UCS4 c;
        {
            // Use tight scope variable to help register allocation.
            Py_UCS4 d = 0;
            for (next = end; next < len; next++) {
                d = PyUnicode_READ(kind, buf, next);
                if (d == '"' || d == '\\') {
                    break;
                }
                if (d <= 0x1f) {
                    if (d == '\n') {
                        raise_errmsg("Unterminated string", pyfilename, pystr, begin, next);
                    }
                    else {
                        raise_errmsg("Unescaped control character", pyfilename, pystr, next, -1);
                    }
                    goto bail;
                }
            }
            c = d;
        }

        if (c == '"') {
            // Fast path for simple case.
            if (writer.buffer == NULL) {
                PyObject *ret = PyUnicode_Substring(pystr, end, next);
                if (ret == NULL) {
                    goto bail;
                }
                *next_end_ptr = next + 1;;
                return ret;
            }
        }
        else if (c != '\\') {
            raise_errmsg("Unterminated string", pyfilename, pystr, begin, next);
            goto bail;
        }

        /* Pick up this chunk if it's not zero length */
        if (next != end) {
            if (_PyUnicodeWriter_WriteSubstring(&writer, pystr, end, next) < 0) {
                goto bail;
            }
        }
        next++;
        if (c == '"') {
            end = next;
            break;
        }
        if (next == len) {
            raise_errmsg("Expecting escaped character", pyfilename, pystr, next, -1);
            goto bail;
        }
        c = PyUnicode_READ(kind, buf, next);
        if (c != 'u') {
            /* Non-unicode backslash escapes */
            end = next + 1;
            switch (c) {
                case '"': break;
                case '\\': break;
                case '/': break;
                case 'b': c = '\b'; break;
                case 'f': c = '\f'; break;
                case 'n': c = '\n'; break;
                case 'r': c = '\r'; break;
                case 't': c = '\t'; break;
                default:
                    if (c == '\n') {
                        raise_errmsg("Expecting escaped character", pyfilename, pystr, end - 1, -1);
                    }
                    else {
                        raise_errmsg("Invalid backslash escape", pyfilename, pystr, end - 2, end);
                    }
                    goto bail;
            }
        }
        else {
            c = 0;
            next++;
            end = next + 4;
            if (end > len) {
                raise_errmsg("Expecting 4 hex digits", pyfilename, pystr, next, next + 4);
                goto bail;
            }
            /* Decode 4 hex digits */
            for (; next < end; next++) {
                Py_UCS4 digit = PyUnicode_READ(kind, buf, next);
                c <<= 4;
                switch (digit) {
                    case '0': case '1': case '2': case '3': case '4':
                    case '5': case '6': case '7': case '8': case '9':
                        c |= (digit - '0'); break;
                    case 'a': case 'b': case 'c': case 'd': case 'e':
                    case 'f':
                        c |= (digit - 'a' + 10); break;
                    case 'A': case 'B': case 'C': case 'D': case 'E':
                    case 'F':
                        c |= (digit - 'A' + 10); break;
                    default:
                        raise_errmsg("Expecting 4 hex digits", pyfilename, pystr, end - 4, end);
                        goto bail;
                }
            }
            /* Surrogate pair */
            if (Py_UNICODE_IS_HIGH_SURROGATE(c) && end + 6 < len &&
                PyUnicode_READ(kind, buf, next++) == '\\' &&
                PyUnicode_READ(kind, buf, next++) == 'u') {
                Py_UCS4 c2 = 0;
                end += 6;
                /* Decode 4 hex digits */
                for (; next < end; next++) {
                    Py_UCS4 digit = PyUnicode_READ(kind, buf, next);
                    c2 <<= 4;
                    switch (digit) {
                        case '0': case '1': case '2': case '3': case '4':
                        case '5': case '6': case '7': case '8': case '9':
                            c2 |= (digit - '0'); break;
                        case 'a': case 'b': case 'c': case 'd': case 'e':
                        case 'f':
                            c2 |= (digit - 'a' + 10); break;
                        case 'A': case 'B': case 'C': case 'D': case 'E':
                        case 'F':
                            c2 |= (digit - 'A' + 10); break;
                        default:
                            raise_errmsg("Expecting 4 hex digits", pyfilename, pystr, end - 4, end);
                            goto bail;
                    }
                }
                if (Py_UNICODE_IS_LOW_SURROGATE(c2))
                    c = Py_UNICODE_JOIN_SURROGATES(c, c2);
                else
                    end -= 6;
            }
        }
        if (_PyUnicodeWriter_WriteChar(&writer, c) < 0) {
            goto bail;
        }
    }

    rval = _PyUnicodeWriter_Finish(&writer);
    *next_end_ptr = end;
    return rval;

bail:
    *next_end_ptr = -1;
    _PyUnicodeWriter_Dealloc(&writer);
    return NULL;
}

PyDoc_STRVAR(pydoc_encode_basestring_ascii,
    "encode_basestring_ascii(string) -> string\n"
    "\n"
    "Return the ASCII-only JSON representation of a Python string"
);

static PyObject *
py_encode_basestring_ascii(PyObject* Py_UNUSED(self), PyObject *pystr)
{
    PyObject *rval;
    /* Return an ASCII-only JSON representation of a Python string */
    /* METH_O */
    if (PyUnicode_Check(pystr)) {
        rval = ascii_escape_unicode(pystr);
    }
    else {
        PyErr_Format(PyExc_TypeError,
                     "first argument must be a string, not %.80s",
                     Py_TYPE(pystr)->tp_name);
        return NULL;
    }
    return rval;
}


PyDoc_STRVAR(pydoc_encode_basestring,
    "encode_basestring(string) -> string\n"
    "\n"
    "Return the JSON representation of a Python string"
);

static PyObject *
py_encode_basestring(PyObject* Py_UNUSED(self), PyObject *pystr)
{
    PyObject *rval;
    /* Return a JSON representation of a Python string */
    /* METH_O */
    if (PyUnicode_Check(pystr)) {
        rval = escape_unicode(pystr);
    }
    else {
        PyErr_Format(PyExc_TypeError,
                     "first argument must be a string, not %.80s",
                     Py_TYPE(pystr)->tp_name);
        return NULL;
    }
    return rval;
}

static void
scanner_dealloc(PyObject *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    /* bpo-31095: UnTrack is needed before calling any callbacks */
    PyObject_GC_UnTrack(self);
    scanner_clear((PyScannerObject *)self);
    tp->tp_free(self);
    Py_DECREF(tp);
}

static int
scanner_traverse(PyScannerObject *self, visitproc visit, void *arg)
{
    Py_VISIT(Py_TYPE(self));
    return 0;
}

static int
scanner_clear(PyScannerObject *self)
{
    return 0;
}

static PyObject *
_parse_object_unicode(PyScannerObject *s, PyObject *memo, PyObject *pyfilename, PyObject *pystr, Py_ssize_t idx, Py_ssize_t *next_idx_ptr)
{
    /* Read a JSON object from PyUnicode pystr.
    idx is the index of the first character after the opening curly brace.
    *next_idx_ptr is a return-by-reference index to the first character after
        the closing curly brace.

    Returns a new dict
    */
    const void *str;
    int kind;
    Py_ssize_t end_idx;
    PyObject *val = NULL;
    PyObject *rval = NULL;
    PyObject *key = NULL;
    Py_ssize_t next_idx;
    Py_ssize_t obj_idx = idx - 1;
    Py_ssize_t colon_idx;
    Py_ssize_t comma_idx;

    str = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);
    end_idx = PyUnicode_GET_LENGTH(pystr) - 1;
    rval = PyDict_New();
    if (rval == NULL)
        return NULL;

    /* skip comments after { */
    if (_skip_comments(s, pyfilename, pystr, &idx)) {
        goto bail;
    }

    /* only loop if the object is non-empty */
    if (idx > end_idx || PyUnicode_READ(kind, str, idx) != '}') {
        while (1) {
            PyObject *new_key;
            if (idx > end_idx) {
                raise_errmsg("Unterminated object", pyfilename, pystr, obj_idx, idx);
                goto bail;
            }

            /* read key */
            if (PyUnicode_READ(kind, str, idx) != '"') {
                raise_errmsg("Expecting string", pyfilename, pystr, idx, -1);
                goto bail;
            }
            key = scanstring_unicode(pyfilename, pystr, idx + 1, &next_idx);
            if (key == NULL)
                goto bail;
            if (!PyDict_Contains(rval, key)) {
                new_key = PyDict_SetDefault(memo, key, key);
            }
            else if (!s->allow_duplicate_keys) {
                raise_errmsg("Duplicate keys are not allowed", pyfilename, pystr, idx, next_idx);
                goto bail;
            }
            else {
                new_key = PyObject_CallOneArg((PyObject *)&PyDuplicateKeyType, key);
            }
            Py_SETREF(key, Py_NewRef(new_key));
            if (key == NULL) {
                goto bail;
            }
            colon_idx = idx = next_idx;

            /* skip comments between key and : delimiter, read :, skip comments */
            if (_skip_comments(s, pyfilename, pystr, &idx)) {
                goto bail;
            }
            if (idx > end_idx || PyUnicode_READ(kind, str, idx) != ':') {
                raise_errmsg("Expecting colon", pyfilename, pystr, colon_idx, -1);
                goto bail;
            }
            idx++;
            if (_skip_comments(s, pyfilename, pystr, &idx)) {
                goto bail;
            }

            /* read any JSON term */
            val = scan_once_unicode(s, memo, pyfilename, pystr, idx, &next_idx);
            if (val == NULL)
                goto bail;

            if (PyDict_SetItem(rval, key, val) < 0)
                goto bail;
            Py_CLEAR(key);
            Py_CLEAR(val);
            comma_idx = idx = next_idx;

            /* skip comments before } or , */
            if (_skip_comments(s, pyfilename, pystr, &idx)) {
                goto bail;
            }

            /* bail if the object is closed or we didn't get the , delimiter */
            if (idx > end_idx) {
                raise_errmsg("Unterminated object", pyfilename, pystr, obj_idx, idx);
                goto bail;
            }
            if (PyUnicode_READ(kind, str, idx) == ',') {
                comma_idx = idx;
                idx++;

                /* skip comments after , delimiter */
                if (_skip_comments(s, pyfilename, pystr, &idx)) {
                    goto bail;
                }
            }
            else if (PyUnicode_READ(kind, str, idx) == '}') {
                break;
            }
            else if (idx == comma_idx) {
                raise_errmsg("Expecting comma", pyfilename, pystr, comma_idx, -1);
                goto bail;
            }
            else if (!s->allow_missing_commas) {
                raise_errmsg("Missing comma's are not allowed", pyfilename, pystr, comma_idx, -1);
                goto bail;
            }

            if (idx <= end_idx && PyUnicode_READ(kind, str, idx) == '}') {
                if (!s->allow_trailing_comma) {
                    raise_errmsg("Trailing comma is not allowed", pyfilename, pystr, comma_idx, -1);
                    goto bail;
                }
                break;
            }
        }
    }

    *next_idx_ptr = idx + 1;
    return rval;
bail:
    Py_XDECREF(key);
    Py_XDECREF(val);
    Py_XDECREF(rval);
    return NULL;
}

static PyObject *
_parse_array_unicode(PyScannerObject *s, PyObject *memo, PyObject *pyfilename, PyObject *pystr, Py_ssize_t idx, Py_ssize_t *next_idx_ptr) {
    /* Read a JSON array from PyUnicode pystr.
    idx is the index of the first character after the opening brace.
    *next_idx_ptr is a return-by-reference index to the first character after
        the closing brace.

    Returns a new PyList
    */
    const void *str;
    int kind;
    Py_ssize_t end_idx;
    PyObject *val = NULL;
    PyObject *rval;
    Py_ssize_t next_idx;
    Py_ssize_t arr_idx = idx - 1;
    Py_ssize_t comma_idx;

    rval = PyList_New(0);
    if (rval == NULL)
        return NULL;

    str = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);
    end_idx = PyUnicode_GET_LENGTH(pystr) - 1;

    /* skip comments after [ */
    if (_skip_comments(s, pyfilename, pystr, &idx)) {
        goto bail;
    }

    /* only loop if the array is non-empty */
    if (idx > end_idx || PyUnicode_READ(kind, str, idx) != ']') {
        while (1) {
            if (idx > end_idx) {
                raise_errmsg("Unterminated array", pyfilename, pystr, arr_idx, idx);
                goto bail;
            }

            /* read any JSON term  */
            val = scan_once_unicode(s, memo, pyfilename, pystr, idx, &next_idx);
            if (val == NULL)
                goto bail;

            if (PyList_Append(rval, val) == -1)
                goto bail;

            Py_CLEAR(val);
            comma_idx = idx = next_idx;

            /* skip comments between term and , */
            if (_skip_comments(s, pyfilename, pystr, &idx)) {
                goto bail;
            }

            /* bail if the array is closed or we didn't get the , delimiter */
            if (idx > end_idx) {
                raise_errmsg("Unterminated array", pyfilename, pystr, arr_idx, idx);
                goto bail;
            }
            if (PyUnicode_READ(kind, str, idx) == ',') {
                comma_idx = idx;
                idx++;

                /* skip comments after , */
                if (_skip_comments(s, pyfilename, pystr, &idx)) {
                    goto bail;
                }
            }
            else if (PyUnicode_READ(kind, str, idx) == ']') {
                break;
            }
            else if (idx == comma_idx) {
                raise_errmsg("Expecting comma", pyfilename, pystr, comma_idx, -1);
                goto bail;
            }
            else if (!s->allow_missing_commas) {
                raise_errmsg("Missing comma's are not allowed", pyfilename, pystr, comma_idx, -1);
                goto bail;
            }

            if (idx <= end_idx && PyUnicode_READ(kind, str, idx) == ']') {
                if (!s->allow_trailing_comma) {
                    raise_errmsg("Trailing comma is not allowed", pyfilename, pystr, comma_idx, -1);
                    goto bail;
                }
                break;
            }
        }
    }

    /* verify that idx < end_idx, PyUnicode_READ(kind, str, idx) should be ']' */
    if (idx > end_idx || PyUnicode_READ(kind, str, idx) != ']') {
        raise_errmsg("Expecting value", pyfilename, pystr, end_idx, -1);
        goto bail;
    }
    *next_idx_ptr = idx + 1;
    return rval;
bail:
    Py_XDECREF(val);
    Py_DECREF(rval);
    return NULL;
}

static PyObject *
_match_number_unicode(PyScannerObject *s, PyObject *pyfilename, PyObject *pystr, Py_ssize_t start, Py_ssize_t *next_idx_ptr) {
    /* Read a JSON number from PyUnicode pystr.
    idx is the index of the first character of the number
    *next_idx_ptr is a return-by-reference index to the first character after
        the number.

    Returns a new PyObject representation of that number: PyLong, or PyFloat.
    */
    const void *str;
    int kind;
    Py_ssize_t end_idx;
    Py_ssize_t idx = start;
    int is_float = 0;
    PyObject *rval;
    PyObject *numstr = NULL;

    str = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);
    end_idx = PyUnicode_GET_LENGTH(pystr) - 1;

    /* read a sign if it's there, make sure it's not the end of the string */
    if (PyUnicode_READ(kind, str, idx) == '-') {
        idx++;
        if (idx > end_idx) {
            raise_errmsg("Expecting value", pyfilename, pystr, start, -1);
            return NULL;
        }
    }

    /* read as many integer digits as we find as long as it doesn't start with 0 */
    if (PyUnicode_READ(kind, str, idx) >= '1' && PyUnicode_READ(kind, str, idx) <= '9') {
        idx++;
        while (idx <= end_idx && PyUnicode_READ(kind, str, idx) >= '0' && PyUnicode_READ(kind, str, idx) <= '9') idx++;
    }
    /* if it starts with 0 we only expect one integer digit */
    else if (PyUnicode_READ(kind, str, idx) == '0') {
        idx++;
    }
    /* no integer digits, error */
    else {
        raise_errmsg("Expecting value", pyfilename, pystr, start, -1);
        return NULL;
    }

    /* if the next char is '.' followed by a digit then read all float digits */
    if (idx < end_idx && PyUnicode_READ(kind, str, idx) == '.' && PyUnicode_READ(kind, str, idx + 1) >= '0' && PyUnicode_READ(kind, str, idx + 1) <= '9') {
        is_float = 1;
        idx += 2;
        while (idx <= end_idx && PyUnicode_READ(kind, str, idx) >= '0' && PyUnicode_READ(kind, str, idx) <= '9') idx++;
    }

    /* if the next char is 'e' or 'E' then maybe read the exponent (or backtrack) */
    if (idx < end_idx && (PyUnicode_READ(kind, str, idx) == 'e' || PyUnicode_READ(kind, str, idx) == 'E')) {
        Py_ssize_t e_start = idx;
        idx++;

        /* read an exponent sign if present */
        if (idx < end_idx && (PyUnicode_READ(kind, str, idx) == '-' || PyUnicode_READ(kind, str, idx) == '+')) idx++;

        /* read all digits */
        while (idx <= end_idx && PyUnicode_READ(kind, str, idx) >= '0' && PyUnicode_READ(kind, str, idx) <= '9') idx++;

        /* if we got a digit, then parse as float. if not, backtrack */
        if (PyUnicode_READ(kind, str, idx - 1) >= '0' && PyUnicode_READ(kind, str, idx - 1) <= '9') {
            is_float = 1;
        }
        else {
            idx = e_start;
        }
    }

    if (is_float && s->use_decimal) {
        /* copy the section we determined to be a number */
        numstr = PyUnicode_FromKindAndData(kind,
                                           (char*)str + kind * start,
                                           idx - start);
        if (numstr == NULL)
            return NULL;
        rval = PyObject_CallOneArg(s->Decimal, numstr);
    }
    else {
        Py_ssize_t i, n;
        char *buf;
        /* Straight conversion to ASCII, to avoid costly conversion of
            decimal unicode digits (which cannot appear here) */
        n = idx - start;
        numstr = PyBytes_FromStringAndSize(NULL, n);
        if (numstr == NULL)
            return NULL;
        buf = PyBytes_AS_STRING(numstr);
        for (i = 0; i < n; i++) {
            buf[i] = (char) PyUnicode_READ(kind, str, i + start);
        }
        if (is_float) {
            rval = PyFloat_FromString(numstr);
            if (!isfinite(PyFloat_AS_DOUBLE(rval))) {
                Py_DECREF(numstr);
                Py_DECREF(rval);
                raise_errmsg("Big numbers require decimal", pyfilename, pystr, start, idx);
                return NULL;
            }
        }
        else
            rval = PyLong_FromString(buf, NULL, 10);
    }
    Py_DECREF(numstr);
    *next_idx_ptr = idx;
    return rval;
}

static PyObject *
scan_once_unicode(PyScannerObject *s, PyObject *memo, PyObject *pyfilename, PyObject *pystr, Py_ssize_t idx, Py_ssize_t *next_idx_ptr)
{
    /* Read one JSON term (of any kind) from PyUnicode pystr.
    idx is the index of the first character of the term
    *next_idx_ptr is a return-by-reference index to the first character after
        the number.

    Returns a new PyObject representation of the term.
    */
    PyObject *numstr;
    PyObject *res;
    const void *str;
    int kind;
    Py_ssize_t length;

    str = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);
    length = PyUnicode_GET_LENGTH(pystr);

    if (idx < 0) {
        PyErr_SetString(PyExc_ValueError, "idx cannot be negative");
        return NULL;
    }
    if (idx >= length) {
        raise_errmsg("Expecting value", pyfilename, pystr, idx, -1);
        return NULL;
    }

    switch (PyUnicode_READ(kind, str, idx)) {
        case '"':
            /* string */
            return scanstring_unicode(pyfilename, pystr, idx + 1, next_idx_ptr);
        case '{':
            /* object */
            if (_Py_EnterRecursiveCall(" while decoding a JSON object "
                                       "from a unicode string"))
                return NULL;
            res = _parse_object_unicode(s, memo, pyfilename, pystr, idx + 1, next_idx_ptr);
            _Py_LeaveRecursiveCall();
            return res;
        case '[':
            /* array */
            if (_Py_EnterRecursiveCall(" while decoding a JSON array "
                                       "from a unicode string"))
                return NULL;
            res = _parse_array_unicode(s, memo, pyfilename, pystr, idx + 1, next_idx_ptr);
            _Py_LeaveRecursiveCall();
            return res;
        case 'n':
            /* null */
            if ((idx + 3 < length) && PyUnicode_READ(kind, str, idx + 1) == 'u' && PyUnicode_READ(kind, str, idx + 2) == 'l' && PyUnicode_READ(kind, str, idx + 3) == 'l') {
                *next_idx_ptr = idx + 4;
                Py_RETURN_NONE;
            }
            break;
        case 't':
            /* true */
            if ((idx + 3 < length) && PyUnicode_READ(kind, str, idx + 1) == 'r' && PyUnicode_READ(kind, str, idx + 2) == 'u' && PyUnicode_READ(kind, str, idx + 3) == 'e') {
                *next_idx_ptr = idx + 4;
                Py_RETURN_TRUE;
            }
            break;
        case 'f':
            /* false */
            if ((idx + 4 < length) && PyUnicode_READ(kind, str, idx + 1) == 'a' &&
                PyUnicode_READ(kind, str, idx + 2) == 'l' &&
                PyUnicode_READ(kind, str, idx + 3) == 's' &&
                PyUnicode_READ(kind, str, idx + 4) == 'e') {
                *next_idx_ptr = idx + 5;
                Py_RETURN_FALSE;
            }
            break;
        case 'N':
            /* NaN */
            if ((idx + 2 < length) && PyUnicode_READ(kind, str, idx + 1) == 'a' &&
                PyUnicode_READ(kind, str, idx + 2) == 'N') {
                if (!s->allow_nan_and_infinity) {
                    raise_errmsg("NaN is not allowed", pyfilename, pystr, idx, idx + 3);
                    return NULL;
                }
                *next_idx_ptr = idx + 3;
                if (s->use_decimal) {
                    numstr = PyUnicode_FromString("NaN");
                    if (numstr == NULL) {
                        return NULL;
                    }
                    return PyObject_CallOneArg(s->Decimal, numstr);
                }
                Py_RETURN_NAN;
            }
            break;
        case 'I':
            /* Infinity */
            if ((idx + 7 < length) && PyUnicode_READ(kind, str, idx + 1) == 'n' &&
                PyUnicode_READ(kind, str, idx + 2) == 'f' &&
                PyUnicode_READ(kind, str, idx + 3) == 'i' &&
                PyUnicode_READ(kind, str, idx + 4) == 'n' &&
                PyUnicode_READ(kind, str, idx + 5) == 'i' &&
                PyUnicode_READ(kind, str, idx + 6) == 't' &&
                PyUnicode_READ(kind, str, idx + 7) == 'y') {
                if (!s->allow_nan_and_infinity) {
                    raise_errmsg("Infinity is not allowed", pyfilename, pystr, idx, idx + 8);
                    return NULL;
                }
                *next_idx_ptr = idx + 8;
                if (s->use_decimal) {
                    numstr = PyUnicode_FromString("Infinity");
                    if (numstr == NULL) {
                        return NULL;
                    }
                    return PyObject_CallOneArg(s->Decimal, numstr);
                }
                Py_RETURN_INF(+1);
            }
            break;
        case '-':
            /* -Infinity */
            if ((idx + 8 < length) && PyUnicode_READ(kind, str, idx + 1) == 'I' &&
                PyUnicode_READ(kind, str, idx + 2) == 'n' &&
                PyUnicode_READ(kind, str, idx + 3) == 'f' &&
                PyUnicode_READ(kind, str, idx + 4) == 'i' &&
                PyUnicode_READ(kind, str, idx + 5) == 'n' &&
                PyUnicode_READ(kind, str, idx + 6) == 'i' &&
                PyUnicode_READ(kind, str, idx + 7) == 't' &&
                PyUnicode_READ(kind, str, idx + 8) == 'y') {
                *next_idx_ptr = idx + 9;
                if (!s->allow_nan_and_infinity) {
                    raise_errmsg("-Infinity is not allowed", pyfilename, pystr, idx, idx + 9);
                    return NULL;
                }
                if (s->use_decimal) {
                    numstr = PyUnicode_FromString("-Infinity");
                    if (numstr == NULL) {
                        return NULL;
                    }
                    return PyObject_CallOneArg(s->Decimal, numstr);
                }
                Py_RETURN_INF(-1);
            }
            break;
    }
    /* Didn't find a string, object, array, or named constant. Look for a number. */
    return _match_number_unicode(s, pyfilename, pystr, idx, next_idx_ptr);
}

static PyObject *
scanner_call(PyScannerObject *self, PyObject *args, PyObject *kwds)
{
    /* Python callable interface to scan_once_{str,unicode} */
    PyObject *pyfilename;
    PyObject *pystr;
    PyObject *rval;
    Py_ssize_t idx = 0;
    Py_ssize_t next_idx = -1;
    static char *kwlist[] = {"filename", "string", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "UU:scan_once", kwlist, &pyfilename, &pystr) ||
        _skip_comments(self, pyfilename, pystr, &idx))
    {
        return NULL;
    }
    PyObject *memo = PyDict_New();
    if (memo == NULL) {
        return NULL;
    }
    rval = scan_once_unicode(self, memo, pyfilename, pystr, idx, &next_idx);
    Py_DECREF(memo);
    if (rval == NULL) {
        return NULL;
    }
    idx = next_idx;
    if (_skip_comments(self, pyfilename, pystr, &idx)) {
        return NULL;
    }
    if (idx < PyUnicode_GET_LENGTH(pystr)) {
        raise_errmsg("Expecting end of file", pyfilename, pystr, idx, -1);
        return NULL;
    }
    return rval;
}

static PyObject *
scanner_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"allow_comments", "allow_duplicate_keys",
                             "allow_missing_commas", "allow_nan_and_infinity",
                             "allow_trailing_comma", "use_decimal", NULL};

    PyScannerObject *s;
    int allow_comments, allow_duplicate_keys, allow_missing_commas;
    int allow_nan_and_infinity, allow_trailing_comma, use_decimal;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "pppppp:make_scanner", kwlist,
        &allow_comments, &allow_duplicate_keys, &allow_missing_commas,
        &allow_nan_and_infinity, &allow_trailing_comma, &use_decimal))
        return NULL;

    s = (PyScannerObject *)type->tp_alloc(type, 0);
    if (s == NULL) {
        return NULL;
    }

    PyObject *decimal = PyImport_ImportModule((char *) "decimal");
    if (decimal == NULL) {
        goto bail;
    }
    s->Decimal = PyObject_GetAttrString(decimal, (char *) "Decimal");
    Py_DECREF(decimal);
    if (s->Decimal == NULL) {
        goto bail;
    }
    s->allow_comments = allow_comments;
    s->allow_duplicate_keys = allow_duplicate_keys;
    s->allow_missing_commas = allow_missing_commas;
    s->allow_nan_and_infinity = allow_nan_and_infinity;
    s->allow_trailing_comma = allow_trailing_comma;
    s->use_decimal = use_decimal;
    return (PyObject *)s;

bail:
    Py_DECREF(s);
    return NULL;
}

PyDoc_STRVAR(scanner_doc, "Make JSON scanner");

static PyType_Slot PyScannerType_slots[] = {
    {Py_tp_doc, (void *)scanner_doc},
    {Py_tp_dealloc, scanner_dealloc},
    {Py_tp_call, scanner_call},
    {Py_tp_traverse, scanner_traverse},
    {Py_tp_clear, scanner_clear},
    {Py_tp_new, scanner_new},
    {0, 0}
};

static PyType_Spec PyScannerType_spec = {
    .name = "_jsonyx.Scanner",
    .basicsize = sizeof(PyScannerObject),
    .itemsize = 0,
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
    .slots = PyScannerType_slots,
};

static PyObject *
encoder_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    static char *kwlist[] = {"encode_decimal", "indent", "key_separator",
                             "item_separator", "sort_keys",
                             "allow_nan_and_infinity", "ensure_ascii", NULL};

    PyEncoderObject *s;
    PyObject *encode_decimal, *indent, *key_separator;
    PyObject *item_separator;
    int sort_keys, allow_nan_and_infinity, ensure_ascii;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOUUppp:make_encoder", kwlist,
        &encode_decimal, &indent,
        &key_separator, &item_separator,
        &sort_keys, &allow_nan_and_infinity, &ensure_ascii))
        return NULL;

    s = (PyEncoderObject *)type->tp_alloc(type, 0);
    if (s == NULL)
        return NULL;

    PyObject *decimal = PyImport_ImportModule((char *) "decimal");
    if (decimal == NULL) {
        goto bail;
    }
    s->Decimal = PyObject_GetAttrString(decimal, (char *) "Decimal");
    Py_DECREF(decimal);
    if (s->Decimal == NULL) {
        goto bail;
    }
    s->encode_decimal = Py_NewRef(encode_decimal);
    s->indent = Py_NewRef(indent);
    s->key_separator = Py_NewRef(key_separator);
    s->item_separator = Py_NewRef(item_separator);
    s->sort_keys = sort_keys;
    s->allow_nan_and_infinity = allow_nan_and_infinity;
    s->ensure_ascii = ensure_ascii;
    return (PyObject *)s;

bail:
    Py_DECREF(s);
    return NULL;
}

static PyObject *
encoder_call(PyEncoderObject *self, PyObject *args, PyObject *kwds)
{
    /* Python callable interface to encode_listencode_obj */
    static char *kwlist[] = {"obj", NULL};
    PyObject *obj;
    _PyUnicodeWriter writer;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:_iterencode", kwlist,
        &obj))
        return NULL;

    _PyUnicodeWriter_Init(&writer);
    writer.overallocate = 1;

    PyObject *newline_indent = NULL;
    PyObject *markers = NULL;
    if (self->indent != Py_None) {
        newline_indent = PyUnicode_FromOrdinal('\n');
        if (newline_indent == NULL) {
            goto bail;
        }
    }
    markers = PyDict_New();
    if (markers == NULL ||
        encoder_listencode_obj(self, markers, &writer, obj, newline_indent))
    {
        goto bail;
    }

    Py_DECREF(markers);
    Py_XDECREF(newline_indent);
    return _PyUnicodeWriter_Finish(&writer);

bail:
    _PyUnicodeWriter_Dealloc(&writer);
    Py_XDECREF(newline_indent);
    Py_XDECREF(markers);
    return NULL;
}

static PyObject *
encoder_encode_float(PyEncoderObject *s, PyObject *obj)
{
    /* Return the JSON representation of a PyFloat. */
    double i = PyFloat_AS_DOUBLE(obj);
    if (!isfinite(i)) {
        if (!s->allow_nan_and_infinity) {
            PyErr_Format(
                    PyExc_ValueError,
                    "%R is not allowed",
                    obj
                    );
            return NULL;
        }
        if (i > 0) {
            return PyUnicode_FromString("Infinity");
        }
        else if (i < 0) {
            return PyUnicode_FromString("-Infinity");
        }
        else {
            return PyUnicode_FromString("NaN");
        }
    }
    return PyFloat_Type.tp_repr(obj);
}

static PyObject *
encoder_encode_string(PyEncoderObject *s, PyObject *obj)
{
    /* Return the JSON representation of a string */
    if (!s->ensure_ascii) {
        return escape_unicode(obj);
    }
    else {
        return ascii_escape_unicode(obj);
    }
}

static int
_steal_accumulate(_PyUnicodeWriter *writer, PyObject *stolen)
{
    /* Append stolen and then decrement its reference count */
    int rval = _PyUnicodeWriter_WriteStr(writer, stolen);
    Py_DECREF(stolen);
    return rval;
}

static int
encoder_listencode_obj(PyEncoderObject *s, PyObject *markers, _PyUnicodeWriter *writer,
                       PyObject *obj, PyObject *newline_indent)
{
    /* Encode Python object obj to a JSON term */
    int rv;

    if (obj == Py_None) {
      return _PyUnicodeWriter_WriteASCIIString(writer, "null", 4);
    }
    else if (obj == Py_True) {
      return _PyUnicodeWriter_WriteASCIIString(writer, "true", 4);
    }
    else if (obj == Py_False) {
      return _PyUnicodeWriter_WriteASCIIString(writer, "false", 5);
    }
    else if (PyUnicode_Check(obj)) {
        PyObject *encoded = encoder_encode_string(s, obj);
        if (encoded == NULL)
            return -1;
        return _steal_accumulate(writer, encoded);
    }
    else if (PyLong_Check(obj)) {
        PyObject *encoded = PyLong_Type.tp_repr(obj);
        if (encoded == NULL)
            return -1;
        return _steal_accumulate(writer, encoded);
    }
    else if (PyFloat_Check(obj)) {
        PyObject *encoded = encoder_encode_float(s, obj);
        if (encoded == NULL)
            return -1;
        return _steal_accumulate(writer, encoded);
    }
    else if (PyList_Check(obj)) {
        if (_Py_EnterRecursiveCall(" while encoding a JSON object"))
            return -1;
        rv = encoder_listencode_list(s, markers, writer, obj, newline_indent);
        _Py_LeaveRecursiveCall();
        return rv;
    }
    else if (PyDict_Check(obj)) {
        if (_Py_EnterRecursiveCall(" while encoding a JSON object"))
            return -1;
        rv = encoder_listencode_dict(s, markers, writer, obj, newline_indent);
        _Py_LeaveRecursiveCall();
        return rv;
    }
    else if (PyObject_TypeCheck(obj, (PyTypeObject *)s->Decimal)) {
        PyObject *encoded = PyObject_CallOneArg(s->encode_decimal, obj);
        if (encoded == NULL)
            return -1;
        return _steal_accumulate(writer, encoded);
    }
    else {
        PyErr_Format(PyExc_TypeError,
                     "%.100s is not JSON serializable", Py_TYPE(obj)->tp_name);
        return -1;
    }
}

static int
encoder_encode_key_value(PyEncoderObject *s, PyObject *markers, _PyUnicodeWriter *writer, bool *first,
                         PyObject *key, PyObject *value,
                         PyObject *newline_indent,
                         PyObject *item_separator)
{
    PyObject *keystr = NULL;
    PyObject *encoded;

    if (PyUnicode_Check(key)) {
        keystr = Py_NewRef(key);
    }
    else {
        PyErr_Format(PyExc_TypeError,
                     "Keys must be str, not %.100s", Py_TYPE(key)->tp_name);
        return -1;
    }

    if (keystr == NULL) {
        return -1;
    }

    if (*first) {
        *first = false;
    }
    else {
        if (_PyUnicodeWriter_WriteStr(writer, item_separator) < 0) {
            Py_DECREF(keystr);
            return -1;
        }
    }

    encoded = encoder_encode_string(s, keystr);
    Py_DECREF(keystr);
    if (encoded == NULL) {
        return -1;
    }

    if (_steal_accumulate(writer, encoded) < 0) {
        return -1;
    }
    if (_PyUnicodeWriter_WriteStr(writer, s->key_separator) < 0) {
        return -1;
    }
    if (encoder_listencode_obj(s, markers, writer, value, newline_indent) < 0) {
        return -1;
    }
    return 0;
}

static int
encoder_listencode_dict(PyEncoderObject *s, PyObject *markers, _PyUnicodeWriter *writer,
                        PyObject *dct, PyObject *newline_indent)
{
    /* Encode Python dict dct a JSON term */
    PyObject *ident = NULL;
    PyObject *items = NULL;
    PyObject *key, *value;
    bool first = true;
    PyObject *new_newline_indent = NULL;
    PyObject *separator_indent = NULL;

    if (PyDict_GET_SIZE(dct) == 0)  /* Fast path */
        return _PyUnicodeWriter_WriteASCIIString(writer, "{}", 2);

    int has_key;
    ident = PyLong_FromVoidPtr(dct);
    if (ident == NULL)
        goto bail;
    has_key = PyDict_Contains(markers, ident);
    if (has_key) {
        if (has_key != -1)
            PyErr_SetString(PyExc_ValueError, "Unexpected circular reference");
        goto bail;
    }
    if (PyDict_SetItem(markers, ident, dct)) {
        goto bail;
    }

    if (_PyUnicodeWriter_WriteChar(writer, '{'))
        goto bail;

    PyObject *current_item_separator = s->item_separator; // borrowed reference
    if (s->indent != Py_None) {
        new_newline_indent = PyUnicode_Concat(newline_indent, s->indent);
        if (new_newline_indent == NULL) {
            goto bail;
        }
        separator_indent = PyUnicode_Concat(current_item_separator, new_newline_indent);
        if (separator_indent == NULL) {
            goto bail;
        }
        // update item separator with a borrowed reference
        current_item_separator = separator_indent;
        if (_PyUnicodeWriter_WriteStr(writer, new_newline_indent) < 0) {
            goto bail;
        }
    }

    if (s->sort_keys || !PyDict_CheckExact(dct)) {
        items = PyMapping_Items(dct);
        if (items == NULL || (s->sort_keys && PyList_Sort(items) < 0))
            goto bail;

        for (Py_ssize_t  i = 0; i < PyList_GET_SIZE(items); i++) {
            PyObject *item = PyList_GET_ITEM(items, i);

            if (!PyTuple_Check(item) || PyTuple_GET_SIZE(item) != 2) {
                PyErr_SetString(PyExc_ValueError, "items must return 2-tuples");
                goto bail;
            }

            key = PyTuple_GET_ITEM(item, 0);
            value = PyTuple_GET_ITEM(item, 1);
            if (encoder_encode_key_value(s, markers, writer, &first, key, value,
                                         new_newline_indent,
                                         current_item_separator) < 0)
                goto bail;
        }
        Py_CLEAR(items);

    } else {
        Py_ssize_t pos = 0;
        while (PyDict_Next(dct, &pos, &key, &value)) {
            if (encoder_encode_key_value(s, markers, writer, &first, key, value,
                                         new_newline_indent,
                                         current_item_separator) < 0)
                goto bail;
        }
    }

    if (PyDict_DelItem(markers, ident))
        goto bail;
    Py_CLEAR(ident);
    if (s->indent != Py_None) {
        Py_CLEAR(new_newline_indent);
        Py_CLEAR(separator_indent);

        if (_PyUnicodeWriter_WriteStr(writer, newline_indent) < 0) {
            goto bail;
        }
    }

    if (_PyUnicodeWriter_WriteChar(writer, '}'))
        goto bail;
    return 0;

bail:
    Py_XDECREF(items);
    Py_XDECREF(ident);
    Py_XDECREF(separator_indent);
    Py_XDECREF(new_newline_indent);
    return -1;
}

static int
encoder_listencode_list(PyEncoderObject *s, PyObject *markers, _PyUnicodeWriter *writer,
                        PyObject *seq, PyObject *newline_indent)
{
    PyObject *ident = NULL;
    PyObject *s_fast = NULL;
    Py_ssize_t i;
    PyObject *new_newline_indent = NULL;
    PyObject *separator_indent = NULL;

    ident = NULL;
    s_fast = PySequence_Fast(seq, "_iterencode_list needs a sequence");
    if (s_fast == NULL)
        return -1;
    if (PySequence_Fast_GET_SIZE(s_fast) == 0) {
        Py_DECREF(s_fast);
        return _PyUnicodeWriter_WriteASCIIString(writer, "[]", 2);
    }

    int has_key;
    ident = PyLong_FromVoidPtr(seq);
    if (ident == NULL)
        goto bail;
    has_key = PyDict_Contains(markers, ident);
    if (has_key) {
        if (has_key != -1)
            PyErr_SetString(PyExc_ValueError, "Unexpected circular reference");
        goto bail;
    }
    if (PyDict_SetItem(markers, ident, seq)) {
        goto bail;
    }

    if (_PyUnicodeWriter_WriteChar(writer, '['))
        goto bail;

    PyObject *separator = s->item_separator; // borrowed reference
    if (s->indent != Py_None) {
        new_newline_indent = PyUnicode_Concat(newline_indent, s->indent);
        if (new_newline_indent == NULL) {
            goto bail;
        }

        if (_PyUnicodeWriter_WriteStr(writer, new_newline_indent) < 0) {
            goto bail;
        }

        separator_indent = PyUnicode_Concat(separator, new_newline_indent);
        if (separator_indent == NULL) {
            goto bail;
        }
        separator = separator_indent; // assign separator with borrowed reference
    }
    for (i = 0; i < PySequence_Fast_GET_SIZE(s_fast); i++) {
        PyObject *obj = PySequence_Fast_GET_ITEM(s_fast, i);
        if (i) {
            if (_PyUnicodeWriter_WriteStr(writer, separator) < 0)
                goto bail;
        }
        if (encoder_listencode_obj(s, markers, writer, obj, new_newline_indent))
            goto bail;
    }
    if (PyDict_DelItem(markers, ident))
        goto bail;
    Py_CLEAR(ident);

    if (s->indent != Py_None) {
        Py_CLEAR(new_newline_indent);
        Py_CLEAR(separator_indent);
        if (_PyUnicodeWriter_WriteStr(writer, newline_indent) < 0) {
            goto bail;
        }
    }

    if (_PyUnicodeWriter_WriteChar(writer, ']'))
        goto bail;
    Py_DECREF(s_fast);
    return 0;

bail:
    Py_XDECREF(ident);
    Py_DECREF(s_fast);
    Py_XDECREF(separator_indent);
    Py_XDECREF(new_newline_indent);
    return -1;
}

static void
encoder_dealloc(PyObject *self)
{
    PyTypeObject *tp = Py_TYPE(self);
    /* bpo-31095: UnTrack is needed before calling any callbacks */
    PyObject_GC_UnTrack(self);
    encoder_clear((PyEncoderObject *)self);
    tp->tp_free(self);
    Py_DECREF(tp);
}

static int
encoder_traverse(PyEncoderObject *self, visitproc visit, void *arg)
{
    Py_VISIT(Py_TYPE(self));
    Py_VISIT(self->encode_decimal);
    Py_VISIT(self->indent);
    Py_VISIT(self->key_separator);
    Py_VISIT(self->item_separator);
    return 0;
}

static int
encoder_clear(PyEncoderObject *self)
{
    /* Deallocate Encoder */
    Py_CLEAR(self->encode_decimal);
    Py_CLEAR(self->indent);
    Py_CLEAR(self->key_separator);
    Py_CLEAR(self->item_separator);
    return 0;
}

PyDoc_STRVAR(encoder_doc, "Make JSON encoder");

static PyType_Slot PyEncoderType_slots[] = {
    {Py_tp_doc, (void *)encoder_doc},
    {Py_tp_dealloc, encoder_dealloc},
    {Py_tp_call, encoder_call},
    {Py_tp_traverse, encoder_traverse},
    {Py_tp_clear, encoder_clear},
    {Py_tp_new, encoder_new},
    {0, 0}
};

static PyType_Spec PyEncoderType_spec = {
    .name = "_jsonyx.Encoder",
    .basicsize = sizeof(PyEncoderObject),
    .itemsize = 0,
    .flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_HAVE_GC,
    .slots = PyEncoderType_slots
};

static PyMethodDef speedups_methods[] = {
    {"encode_basestring_ascii",
        (PyCFunction)py_encode_basestring_ascii,
        METH_O,
        pydoc_encode_basestring_ascii},
    {"encode_basestring",
        (PyCFunction)py_encode_basestring,
        METH_O,
        pydoc_encode_basestring},
    {NULL, NULL, 0, NULL}
};

PyDoc_STRVAR(module_doc,
"json speedups\n");

static int
_json_exec(PyObject *module)
{
    PyObject *PyScannerType = PyType_FromSpec(&PyScannerType_spec);
    if (PyScannerType == NULL) {
        return -1;
    }
    int rc = PyModule_AddObjectRef(module, "make_scanner", PyScannerType);
    Py_DECREF(PyScannerType);
    if (rc < 0) {
        return -1;
    }

    PyObject *PyEncoderType = PyType_FromSpec(&PyEncoderType_spec);
    if (PyEncoderType == NULL) {
        return -1;
    }
    rc = PyModule_AddObjectRef(module, "make_encoder", PyEncoderType);
    Py_DECREF(PyEncoderType);
    if (rc < 0) {
        return -1;
    }

    PyDuplicateKeyType.tp_base = &PyUnicode_Type;
    if (PyType_Ready(&PyDuplicateKeyType) < 0) {
        return -1;
    }
    Py_INCREF(&PyDuplicateKeyType);
    rc = PyModule_AddObject(module, "DuplicateKey", (PyObject *) &PyDuplicateKeyType);
    if (rc < 0) {
        Py_DECREF(&PyDuplicateKeyType);
        return -1;
    }

    return 0;
}

static PyModuleDef_Slot _json_slots[] = {
    {Py_mod_exec, _json_exec},
#if defined Py_mod_multiple_interpreters && defined Py_MOD_PER_INTERPRETER_GIL_SUPPORTED
    {Py_mod_multiple_interpreters, Py_MOD_PER_INTERPRETER_GIL_SUPPORTED},
#endif
#if defined Py_mod_gil && defined Py_MOD_GIL_NOT_USED
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
#endif
    {0, NULL}
};

static struct PyModuleDef jsonmodule = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "_jsonyx",
    .m_doc = module_doc,
    .m_methods = speedups_methods,
    .m_slots = _json_slots,
};

PyMODINIT_FUNC
PyInit__jsonyx(void)
{
    return PyModuleDef_Init(&jsonmodule);
}