#include <Python.h>

static PyObject*
hello_world_impl(PyObject* module)
{
    return PyUnicode_FromString("hello world");
}

static struct PyMethodDef hello_methods[] = {
    {"hello_world", (PyCFunction)hello_world_impl, METH_NOARGS, "Return hello world."},
    {NULL, NULL}
};

static struct PyModuleDef hellomodule = {
    .m_base = PyModuleDef_HEAD_INIT,
    .m_name = "_hello",
    .m_doc = "C implementation of the hello module.",
    .m_methods = hello_methods
};

PyMODINIT_FUNC
PyInit__hello(void)
{
    return PyModule_Create(&hellomodule);
}