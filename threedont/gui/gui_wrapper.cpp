#include <Python.h>
#include <QApplication>
#include <QDebug>
#include <iostream>
#include "main_layout.h"

typedef struct {
    PyObject_HEAD
    PyObject *executeQueryCallback;
    MainLayout *mainLayout;
    QApplication *app;
} GuiWrapperObject;

static void GuiWrapper_dealloc(GuiWrapperObject *self) {
    Py_XDECREF(self->executeQueryCallback);
    Py_TYPE(self)->tp_free((PyObject *) self);
    delete self->mainLayout;
    delete self->app;
}

static PyObject *GuiWrapper_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    GuiWrapperObject *self;
    self = (GuiWrapperObject *) type->tp_alloc(type, 0);
    if (self != nullptr) {
        self->executeQueryCallback = nullptr;
        self->mainLayout = nullptr;
    }
    return (PyObject *) self;
}

static int GuiWrapper_init(GuiWrapperObject *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {"executeQueryCallback", "portNumber", nullptr};
    PyObject *executeQueryCallback = nullptr;
    int portNumber;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Oi", kwlist, &executeQueryCallback, &portNumber)) {
        return -1;
    }

    if (!PyCallable_Check(executeQueryCallback)) {
        PyErr_SetString(PyExc_TypeError, "Parameter must be callable");
        return -1;
    }

    self->executeQueryCallback = executeQueryCallback;
    Py_XINCREF(executeQueryCallback);
    self->mainLayout = new MainLayout(portNumber, [self](const std::string& query) {
        PyObject *arglist = Py_BuildValue("(s)", query.c_str());
        PyObject *result = PyObject_CallObject(self->executeQueryCallback, arglist);
        Py_XDECREF(arglist);
        Py_XDECREF(result);
    });

    int zero = 0; // hack to get QApplication to work
    self->app = new QApplication(zero, nullptr);

    return 0;
}

static PyObject *GuiWrapper_exec(GuiWrapperObject *self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    if (self->app == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "QApplication not initialized");
        return nullptr;
    }

    QApplication::exec();
    return Py_None;
}

static PyMethodDef GuiWrapper_methods[] = {
        {"exec", (PyCFunction) GuiWrapper_exec, METH_NOARGS, "Starts the GUI event loop"},
        {nullptr}
};

static PyTypeObject GuiWrapperType = {
        .ob_base = PyVarObject_HEAD_INIT(nullptr, 0)
        .tp_name = "gui.GuiWrapper",
        .tp_basicsize = sizeof(GuiWrapperObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor) GuiWrapper_dealloc,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = "Wrapper for the GUI",
        .tp_methods = GuiWrapper_methods,
        .tp_init = (initproc) GuiWrapper_init,
        .tp_new = GuiWrapper_new
};

static PyModuleDef guimodule = {
        PyModuleDef_HEAD_INIT,
        .m_name = "gui",
        .m_doc = "Gui bindings for 3dont",
        .m_size = -1
};

PyMODINIT_FUNC PyInit_gui(void) {
    PyObject *m;
    if (PyType_Ready(&GuiWrapperType) < 0) {
        return nullptr;
    }

    m = PyModule_Create(&guimodule);
    if (m == nullptr) {
        return nullptr;
    }

    Py_INCREF(&GuiWrapperType);
    PyModule_AddObject(m, "GuiWrapper", (PyObject *) &GuiWrapperType);
    return m;
}

