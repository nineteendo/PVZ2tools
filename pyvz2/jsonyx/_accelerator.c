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
    int allow_comments;
    int allow_duplicate_keys;
    int allow_nan;
    int allow_trailing_comma;
} PyScannerObject;

static PyMemberDef scanner_members[] = {
    {"allow_comments", Py_T_BOOL, offsetof(PyScannerObject, allow_comments), Py_READONLY, "allow_comments"},
    {"allow_duplicate_keys", Py_T_BOOL, offsetof(PyScannerObject, allow_duplicate_keys), Py_READONLY, "allow_duplicate_keys"},
    {"allow_nan", Py_T_BOOL, offsetof(PyScannerObject, allow_nan), Py_READONLY, "allow_nan"},
    {"allow_trailing_comma", Py_T_BOOL, offsetof(PyScannerObject, allow_trailing_comma), Py_READONLY, "allow_trailing_comma"},
    {NULL}
};

typedef struct _PyEncoderObject {
    PyObject_HEAD
    PyObject *markers;
    PyObject *defaultfn;
    PyObject *encoder;
    PyObject *indent;
    PyObject *key_separator;
    PyObject *item_separator;
    char sort_keys;
    char skipkeys;
    int allow_nan;
    PyCFunction fast_encode;
} PyEncoderObject;

static PyMemberDef encoder_members[] = {
    {"markers", _Py_T_OBJECT, offsetof(PyEncoderObject, markers), Py_READONLY, "markers"},
    {"default", _Py_T_OBJECT, offsetof(PyEncoderObject, defaultfn), Py_READONLY, "default"},
    {"encoder", _Py_T_OBJECT, offsetof(PyEncoderObject, encoder), Py_READONLY, "encoder"},
    {"indent", _Py_T_OBJECT, offsetof(PyEncoderObject, indent), Py_READONLY, "indent"},
    {"key_separator", _Py_T_OBJECT, offsetof(PyEncoderObject, key_separator), Py_READONLY, "key_separator"},
    {"item_separator", _Py_T_OBJECT, offsetof(PyEncoderObject, item_separator), Py_READONLY, "item_separator"},
    {"sort_keys", Py_T_BOOL, offsetof(PyEncoderObject, sort_keys), Py_READONLY, "sort_keys"},
    {"skipkeys", Py_T_BOOL, offsetof(PyEncoderObject, skipkeys), Py_READONLY, "skipkeys"},
    {NULL}
};

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
_build_rval_index_tuple(PyObject *rval, Py_ssize_t idx);
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
encoder_listencode_list(PyEncoderObject *s, _PyUnicodeWriter *writer, PyObject *seq, PyObject *newline_indent);
static int
encoder_listencode_obj(PyEncoderObject *s, _PyUnicodeWriter *writer, PyObject *obj, PyObject *newline_indent);
static int
encoder_listencode_dict(PyEncoderObject *s, _PyUnicodeWriter *writer, PyObject *dct, PyObject *newline_indent);
static PyObject *
_encoded_const(PyObject *obj);
static void
raise_errmsg(const char *msg, PyObject *filename, PyObject *s, Py_ssize_t end);
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
        if (idx + 1 < len && PyUnicode_READ(kind, str, idx) == '/' &&
            PyUnicode_READ(kind, str, idx + 1) == '/')
        {
            if (!s->allow_comments) {
                raise_errmsg("Comments aren't allowed", pyfilename, pystr, idx);
                return -1;
            }
            idx += 2;
            while (idx < len && PyUnicode_READ(kind,str, idx) != '\n') {
                idx++;
            }
        }
        else if (idx + 1 < len && PyUnicode_READ(kind, str, idx) == '/' &&
                 PyUnicode_READ(kind, str, idx + 1) == '*')
        {
            if (!s->allow_comments) {
                raise_errmsg("Comments aren't allowed", pyfilename, pystr, idx);
                return -1;
            }
            comment_idx = idx;
            idx += 2;
            while (1) {
                if (idx + 1 >= len) {
                    raise_errmsg("Unterminated comment", pyfilename, pystr, comment_idx);
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
raise_errmsg(const char *msg, PyObject *filename, PyObject *s, Py_ssize_t end)
{
    /* Use JSONSyntaxError exception to raise a nice looking SyntaxError subclass */
    PyObject *JSONSyntaxError = _PyImport_GetModuleAttrString("jsonyx.scanner",
                                                              "JSONSyntaxError");
    if (JSONSyntaxError == NULL) {
        return;
    }

    PyObject *exc;
    exc = PyObject_CallFunction(JSONSyntaxError, "zOOn", msg, filename, s, end);
    Py_DECREF(JSONSyntaxError);
    if (exc) {
        PyErr_SetObject(JSONSyntaxError, exc);
        Py_DECREF(exc);
    }
}

static PyObject *
_build_rval_index_tuple(PyObject *rval, Py_ssize_t idx) {
    /* return (rval, idx) tuple, stealing reference to rval */
    PyObject *tpl;
    PyObject *pyidx;
    /*
    steal a reference to rval, returns (rval, idx)
    */
    if (rval == NULL) {
        return NULL;
    }
    pyidx = PyLong_FromSsize_t(idx);
    if (pyidx == NULL) {
        Py_DECREF(rval);
        return NULL;
    }
    tpl = PyTuple_New(2);
    if (tpl == NULL) {
        Py_DECREF(pyidx);
        Py_DECREF(rval);
        return NULL;
    }
    PyTuple_SET_ITEM(tpl, 0, rval);
    PyTuple_SET_ITEM(tpl, 1, pyidx);
    return tpl;
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
                        raise_errmsg("Unterminated string", pyfilename, pystr, begin);
                    }
                    else {
                        raise_errmsg("Unescaped control character", pyfilename, pystr, next);
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
            raise_errmsg("Unterminated string", pyfilename, pystr, begin);
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
            raise_errmsg("Invalid backslash escape", pyfilename, pystr, next);
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
                default: c = 0;
            }
            if (c == 0) {
                raise_errmsg("Invalid backslash escape", pyfilename, pystr, end - 1);
                goto bail;
            }
        }
        else {
            c = 0;
            next++;
            end = next + 4;
            if (end > len) {
                raise_errmsg("Expecting 4 hex digits", pyfilename, pystr, next);
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
                        raise_errmsg("Expecting 4 hex digits", pyfilename, pystr, end - 4);
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
                            raise_errmsg("Expecting 4 hex digits", pyfilename, pystr, end - 4);
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

PyDoc_STRVAR(pydoc_scanstring,
    "scanstring(string, end) -> (string, end)\n"
    "\n"
    "Scan the string s for a JSON string. End is the index of the\n"
    "character in s after the quote that started the JSON string.\n"
    "Unescapes all valid JSON string escape sequences and raises ValueError\n"
    "on attempt to decode an invalid string.\n"
    "\n"
    "Returns a tuple of the decoded string and the index of the character in s\n"
    "after the end quote."
);

static PyObject *
py_scanstring(PyObject* Py_UNUSED(self), PyObject *args)
{
    PyObject *pyfilename;
    PyObject *pystr;
    PyObject *rval;
    Py_ssize_t end;
    Py_ssize_t next_end = -1;
    if (!PyArg_ParseTuple(args, "OOn|p:scanstring", &pyfilename, &pystr, &end)) {
        return NULL;
    }
    if (!PyUnicode_Check(pyfilename)) {
        PyErr_Format(PyExc_TypeError,
                     "first argument must be a string, not %.80s",
                     Py_TYPE(pyfilename)->tp_name);
        return NULL;
    }
    if (PyUnicode_Check(pystr)) {
        rval = scanstring_unicode(pyfilename, pystr, end, &next_end);
    }
    else {
        PyErr_Format(PyExc_TypeError,
                     "second argument must be a string, not %.80s",
                     Py_TYPE(pystr)->tp_name);
        return NULL;
    }
    return _build_rval_index_tuple(rval, next_end);
}

PyDoc_STRVAR(pydoc_encode_basestring_ascii,
    "encode_basestring_ascii(string) -> string\n"
    "\n"
    "Return an ASCII-only JSON representation of a Python string"
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
    "Return a JSON representation of a Python string"
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

            /* read key */
            if (idx > end_idx || PyUnicode_READ(kind, str, idx) != '"') {
                raise_errmsg("Expecting string", pyfilename, pystr, idx);
                goto bail;
            }
            key = scanstring_unicode(pyfilename, pystr, idx + 1, &next_idx);
            if (key == NULL)
                goto bail;
            if (!PyDict_Contains(rval, key)) {
                new_key = PyDict_SetDefault(memo, key, key);
            }
            else  if (!s->allow_duplicate_keys) {
                raise_errmsg("Duplicate keys aren't allowed", pyfilename, pystr, idx);
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
                raise_errmsg("Expecting ':' delimiter", pyfilename, pystr, colon_idx);
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
            if (idx <= end_idx && PyUnicode_READ(kind, str, idx) == '}')
                break;
            if (idx > end_idx || PyUnicode_READ(kind, str, idx) != ',') {
                raise_errmsg("Expecting ',' delimiter", pyfilename, pystr, comma_idx);
                goto bail;
            }
            comma_idx = idx;
            idx++;

            /* skip comments after , delimiter */
            if (_skip_comments(s, pyfilename, pystr, &idx)) {
                goto bail;
            }

            if (idx <= end_idx && PyUnicode_READ(kind, str, idx) == '}') {
                if (s->allow_trailing_comma) {
                    break;
                }
                raise_errmsg("Trailing comma's aren't allowed", pyfilename, pystr, comma_idx);
                goto bail;
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
            if (idx <= end_idx && PyUnicode_READ(kind, str, idx) == ']')
                break;
            if (idx > end_idx || PyUnicode_READ(kind, str, idx) != ',') {
                raise_errmsg("Expecting ',' delimiter", pyfilename, pystr, comma_idx);
                goto bail;
            }
            comma_idx = idx;
            idx++;

            /* skip comments after , */
            if (_skip_comments(s, pyfilename, pystr, &idx)) {
                goto bail;
            }

            if (idx <= end_idx && PyUnicode_READ(kind, str, idx) == ']') {
                if (s->allow_trailing_comma) {
                    break;
                }
                raise_errmsg("Trailing comma's aren't allowed", pyfilename, pystr, comma_idx);
                goto bail;
            }
        }
    }

    /* verify that idx < end_idx, PyUnicode_READ(kind, str, idx) should be ']' */
    if (idx > end_idx || PyUnicode_READ(kind, str, idx) != ']') {
        raise_errmsg("Expecting value", pyfilename, pystr, end_idx);
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
    PyObject *custom_func;

    str = PyUnicode_DATA(pystr);
    kind = PyUnicode_KIND(pystr);
    end_idx = PyUnicode_GET_LENGTH(pystr) - 1;

    /* read a sign if it's there, make sure it's not the end of the string */
    if (PyUnicode_READ(kind, str, idx) == '-') {
        idx++;
        if (idx > end_idx) {
            raise_errmsg("Expecting value", pyfilename, pystr, start);
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
        raise_errmsg("Expecting value", pyfilename, pystr, start);
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
    if (is_float)
        rval = PyFloat_FromString(numstr);
    else
        rval = PyLong_FromString(buf, NULL, 10);
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
        raise_errmsg("Expecting value", pyfilename, pystr, idx);
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
                if (!s->allow_nan) {
                    raise_errmsg("NaN isn't allowed", pyfilename, pystr, idx - 1);
                    return NULL;
                }
                *next_idx_ptr = idx + 3;
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
                if (!s->allow_nan) {
                    raise_errmsg("Infinity isn't allowed", pyfilename, pystr, idx - 1);
                    return NULL;
                }
                *next_idx_ptr = idx + 8;
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
                if (!s->allow_nan) {
                    raise_errmsg("Infinity isn't allowed", pyfilename, pystr, idx - 1);
                    return NULL;
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
    Py_ssize_t idx;
    Py_ssize_t next_idx = -1;
    static char *kwlist[] = {"filename", "string", "idx", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOn:scan_once", kwlist, &pyfilename, &pystr, &idx))
        return NULL;

    if (!PyUnicode_Check(pyfilename)) {
        PyErr_Format(PyExc_TypeError,
                 "first argument must be a string, not %.80s",
                 Py_TYPE(pyfilename)->tp_name);
        return NULL;
    }
    if (!PyUnicode_Check(pystr)) {
        PyErr_Format(PyExc_TypeError,
                 "second argument must be a string, not %.80s",
                 Py_TYPE(pystr)->tp_name);
        return NULL;
    }

    PyObject *memo = PyDict_New();
    if (memo == NULL) {
        return NULL;
    }
    rval = scan_once_unicode(self, memo, pyfilename, pystr, idx, &next_idx);
    Py_DECREF(memo);
    if (rval == NULL)
        return NULL;
    return _build_rval_index_tuple(rval, next_idx);
}

static PyObject *
scanner_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
{
    PyScannerObject *s;
    PyObject *ctx;
    PyObject *allow_comments;
    PyObject *allow_duplicate_keys;
    PyObject *allow_nan;
    PyObject *allow_trailing_comma;
    static char *kwlist[] = {"context", NULL};

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O:make_scanner", kwlist, &ctx))
        return NULL;

    s = (PyScannerObject *)type->tp_alloc(type, 0);
    if (s == NULL) {
        return NULL;
    }

    /* All of these will fail "gracefully" so we don't need to verify them */
    allow_comments = PyObject_GetAttrString(ctx, "allow_comments");
    if (allow_comments == NULL)
        goto bail;
    s->allow_comments = PyObject_IsTrue(allow_comments);
    Py_DECREF(allow_comments);
    if (s->allow_comments < 0)
        goto bail;
    allow_duplicate_keys = PyObject_GetAttrString(ctx, "allow_duplicate_keys");
    if (allow_duplicate_keys == NULL)
        goto bail;
    s->allow_duplicate_keys = PyObject_IsTrue(allow_duplicate_keys);
    Py_DECREF(allow_duplicate_keys);
    if (s->allow_duplicate_keys < 0)
        goto bail;
    allow_nan = PyObject_GetAttrString(ctx, "allow_nan");
    if (allow_nan == NULL)
        goto bail;
    s->allow_nan = PyObject_IsTrue(allow_nan);
    Py_DECREF(allow_nan);
    if (s->allow_nan < 0)
        goto bail;
    allow_trailing_comma = PyObject_GetAttrString(ctx, "allow_trailing_comma");
    if (allow_trailing_comma == NULL)
        goto bail;
    s->allow_trailing_comma = PyObject_IsTrue(allow_trailing_comma);
    Py_DECREF(allow_trailing_comma);
    if (s->allow_trailing_comma < 0)
        goto bail;
    return (PyObject *)s;

bail:
    Py_DECREF(s);
    return NULL;
}

PyDoc_STRVAR(scanner_doc, "JSON scanner object");

static PyType_Slot PyScannerType_slots[] = {
    {Py_tp_doc, (void *)scanner_doc},
    {Py_tp_dealloc, scanner_dealloc},
    {Py_tp_call, scanner_call},
    {Py_tp_traverse, scanner_traverse},
    {Py_tp_clear, scanner_clear},
    {Py_tp_members, scanner_members},
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
    static char *kwlist[] = {"markers", "default", "encoder", "indent", "key_separator", "item_separator", "sort_keys", "skipkeys", "allow_nan", NULL};

    PyEncoderObject *s;
    PyObject *markers, *defaultfn, *encoder, *indent, *key_separator;
    PyObject *item_separator;
    int sort_keys, skipkeys, allow_nan;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOOOUUppp:make_encoder", kwlist,
        &markers, &defaultfn, &encoder, &indent,
        &key_separator, &item_separator,
        &sort_keys, &skipkeys, &allow_nan))
        return NULL;

    if (markers != Py_None && !PyDict_Check(markers)) {
        PyErr_Format(PyExc_TypeError,
                     "make_encoder() argument 1 must be dict or None, "
                     "not %.200s", Py_TYPE(markers)->tp_name);
        return NULL;
    }

    s = (PyEncoderObject *)type->tp_alloc(type, 0);
    if (s == NULL)
        return NULL;

    s->markers = Py_NewRef(markers);
    s->defaultfn = Py_NewRef(defaultfn);
    s->encoder = Py_NewRef(encoder);
    s->indent = Py_NewRef(indent);
    s->key_separator = Py_NewRef(key_separator);
    s->item_separator = Py_NewRef(item_separator);
    s->sort_keys = sort_keys;
    s->skipkeys = skipkeys;
    s->allow_nan = allow_nan;
    s->fast_encode = NULL;

    if (PyCFunction_Check(s->encoder)) {
        PyCFunction f = PyCFunction_GetFunction(s->encoder);
        if (f == (PyCFunction)py_encode_basestring_ascii ||
                f == (PyCFunction)py_encode_basestring) {
            s->fast_encode = f;
        }
    }

    return (PyObject *)s;
}

static PyObject *
_create_newline_indent(PyObject *indent, Py_ssize_t indent_level)
{
    PyObject *newline_indent = PyUnicode_FromOrdinal('\n');
    if (newline_indent != NULL && indent_level) {
        PyUnicode_AppendAndDel(&newline_indent,
                               PySequence_Repeat(indent, indent_level));
    }
    return newline_indent;
}

static PyObject *
encoder_call(PyEncoderObject *self, PyObject *args, PyObject *kwds)
{
    /* Python callable interface to encode_listencode_obj */
    static char *kwlist[] = {"obj", "_current_indent_level", NULL};
    PyObject *obj, *result;
    Py_ssize_t indent_level;
    _PyUnicodeWriter writer;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "On:_iterencode", kwlist,
        &obj, &indent_level))
        return NULL;

    _PyUnicodeWriter_Init(&writer);
    writer.overallocate = 1;

    PyObject *newline_indent = NULL;
    if (self->indent != Py_None) {
        newline_indent = _create_newline_indent(self->indent, indent_level);
        if (newline_indent == NULL) {
            _PyUnicodeWriter_Dealloc(&writer);
            return NULL;
        }
    }
    if (encoder_listencode_obj(self, &writer, obj, newline_indent)) {
        _PyUnicodeWriter_Dealloc(&writer);
        Py_XDECREF(newline_indent);
        return NULL;
    }
    Py_XDECREF(newline_indent);

    result = PyTuple_New(1);
    if (result == NULL ||
            PyTuple_SetItem(result, 0, _PyUnicodeWriter_Finish(&writer)) < 0) {
        Py_XDECREF(result);
        return NULL;
    }
    return result;
}

static PyObject *
_encoded_const(PyObject *obj)
{
    /* Return the JSON string representation of None, True, False */
    if (obj == Py_None) {
        return PyUnicode_FromString("None");
    }
    else if (obj == Py_True) {
        return PyUnicode_FromString("True");
    }
    else if (obj == Py_False) {
        return PyUnicode_FromString("False");
    }
    else {
        PyErr_SetString(PyExc_ValueError, "not a const");
        return NULL;
    }
}

static PyObject *
encoder_encode_float(PyEncoderObject *s, PyObject *obj)
{
    /* Return the JSON representation of a PyFloat. */
    double i = PyFloat_AS_DOUBLE(obj);
    if (!isfinite(i)) {
        if (!s->allow_nan) {
            PyErr_Format(
                    PyExc_ValueError,
                    "Out of range float values are not JSON compliant: %R",
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
    PyObject *encoded;

    if (s->fast_encode) {
        return s->fast_encode(NULL, obj);
    }
    encoded = PyObject_CallOneArg(s->encoder, obj);
    if (encoded != NULL && !PyUnicode_Check(encoded)) {
        PyErr_Format(PyExc_TypeError,
                     "encoder() must return a string, not %.80s",
                     Py_TYPE(encoded)->tp_name);
        Py_DECREF(encoded);
        return NULL;
    }
    return encoded;
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
encoder_listencode_obj(PyEncoderObject *s, _PyUnicodeWriter *writer,
                       PyObject *obj, PyObject *newline_indent)
{
    /* Encode Python object obj to a JSON term */
    PyObject *newobj;
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
    else if (PyList_Check(obj) || PyTuple_Check(obj)) {
        if (_Py_EnterRecursiveCall(" while encoding a JSON object"))
            return -1;
        rv = encoder_listencode_list(s, writer, obj, newline_indent);
        _Py_LeaveRecursiveCall();
        return rv;
    }
    else if (PyDict_Check(obj)) {
        if (_Py_EnterRecursiveCall(" while encoding a JSON object"))
            return -1;
        rv = encoder_listencode_dict(s, writer, obj, newline_indent);
        _Py_LeaveRecursiveCall();
        return rv;
    }
    else {
        PyObject *ident = NULL;
        if (s->markers != Py_None) {
            int has_key;
            ident = PyLong_FromVoidPtr(obj);
            if (ident == NULL)
                return -1;
            has_key = PyDict_Contains(s->markers, ident);
            if (has_key) {
                if (has_key != -1)
                    PyErr_SetString(PyExc_ValueError, "Circular reference detected");
                Py_DECREF(ident);
                return -1;
            }
            if (PyDict_SetItem(s->markers, ident, obj)) {
                Py_DECREF(ident);
                return -1;
            }
        }
        newobj = PyObject_CallOneArg(s->defaultfn, obj);
        if (newobj == NULL) {
            Py_XDECREF(ident);
            return -1;
        }

        if (_Py_EnterRecursiveCall(" while encoding a JSON object")) {
            Py_DECREF(newobj);
            Py_XDECREF(ident);
            return -1;
        }
        rv = encoder_listencode_obj(s, writer, newobj, newline_indent);
        _Py_LeaveRecursiveCall();

        Py_DECREF(newobj);
        if (rv) {
            Py_XDECREF(ident);
            return -1;
        }
        if (ident != NULL) {
            if (PyDict_DelItem(s->markers, ident)) {
                Py_XDECREF(ident);
                return -1;
            }
            Py_XDECREF(ident);
        }
        return rv;
    }
}

static int
encoder_encode_key_value(PyEncoderObject *s, _PyUnicodeWriter *writer, bool *first,
                         PyObject *key, PyObject *value,
                         PyObject *newline_indent,
                         PyObject *item_separator)
{
    PyObject *keystr = NULL;
    PyObject *encoded;

    if (PyUnicode_Check(key)) {
        keystr = Py_NewRef(key);
    }
    else if (PyFloat_Check(key)) {
        keystr = encoder_encode_float(s, key);
    }
    else if (key == Py_True || key == Py_False || key == Py_None) {
                    /* This must come before the PyLong_Check because
                       True and False are also 1 and 0.*/
        keystr = _encoded_const(key);
    }
    else if (PyLong_Check(key)) {
        keystr = PyLong_Type.tp_repr(key);
    }
    else if (s->skipkeys) {
        return 0;
    }
    else {
        PyErr_Format(PyExc_TypeError,
                     "keys must be str, int, float, bool or None, "
                     "not %.100s", Py_TYPE(key)->tp_name);
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
    if (encoder_listencode_obj(s, writer, value, newline_indent) < 0) {
        return -1;
    }
    return 0;
}

static int
encoder_listencode_dict(PyEncoderObject *s, _PyUnicodeWriter *writer,
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

    if (s->markers != Py_None) {
        int has_key;
        ident = PyLong_FromVoidPtr(dct);
        if (ident == NULL)
            goto bail;
        has_key = PyDict_Contains(s->markers, ident);
        if (has_key) {
            if (has_key != -1)
                PyErr_SetString(PyExc_ValueError, "Circular reference detected");
            goto bail;
        }
        if (PyDict_SetItem(s->markers, ident, dct)) {
            goto bail;
        }
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
            if (encoder_encode_key_value(s, writer, &first, key, value,
                                         new_newline_indent,
                                         current_item_separator) < 0)
                goto bail;
        }
        Py_CLEAR(items);

    } else {
        Py_ssize_t pos = 0;
        while (PyDict_Next(dct, &pos, &key, &value)) {
            if (encoder_encode_key_value(s, writer, &first, key, value,
                                         new_newline_indent,
                                         current_item_separator) < 0)
                goto bail;
        }
    }

    if (ident != NULL) {
        if (PyDict_DelItem(s->markers, ident))
            goto bail;
        Py_CLEAR(ident);
    }
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
encoder_listencode_list(PyEncoderObject *s, _PyUnicodeWriter *writer,
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

    if (s->markers != Py_None) {
        int has_key;
        ident = PyLong_FromVoidPtr(seq);
        if (ident == NULL)
            goto bail;
        has_key = PyDict_Contains(s->markers, ident);
        if (has_key) {
            if (has_key != -1)
                PyErr_SetString(PyExc_ValueError, "Circular reference detected");
            goto bail;
        }
        if (PyDict_SetItem(s->markers, ident, seq)) {
            goto bail;
        }
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
        if (encoder_listencode_obj(s, writer, obj, new_newline_indent))
            goto bail;
    }
    if (ident != NULL) {
        if (PyDict_DelItem(s->markers, ident))
            goto bail;
        Py_CLEAR(ident);
    }

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
    Py_VISIT(self->markers);
    Py_VISIT(self->defaultfn);
    Py_VISIT(self->encoder);
    Py_VISIT(self->indent);
    Py_VISIT(self->key_separator);
    Py_VISIT(self->item_separator);
    return 0;
}

static int
encoder_clear(PyEncoderObject *self)
{
    /* Deallocate Encoder */
    Py_CLEAR(self->markers);
    Py_CLEAR(self->defaultfn);
    Py_CLEAR(self->encoder);
    Py_CLEAR(self->indent);
    Py_CLEAR(self->key_separator);
    Py_CLEAR(self->item_separator);
    return 0;
}

PyDoc_STRVAR(encoder_doc, "Encoder(markers, default, encoder, indent, key_separator, item_separator, sort_keys, skipkeys, allow_nan)");

static PyType_Slot PyEncoderType_slots[] = {
    {Py_tp_doc, (void *)encoder_doc},
    {Py_tp_dealloc, encoder_dealloc},
    {Py_tp_call, encoder_call},
    {Py_tp_traverse, encoder_traverse},
    {Py_tp_clear, encoder_clear},
    {Py_tp_members, encoder_members},
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
    {"scanstring",
        (PyCFunction)py_scanstring,
        METH_VARARGS,
        pydoc_scanstring},
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