#include <Python.h>
#include <QApplication>
#include <iostream>
#include "main_layout.h"
#include "controller_wrapper.h"
#include <csignal>

typedef struct {
    PyObject_HEAD
    ControllerWrapper *controllerWrapper;
    MainLayout *mainLayout;
    QApplication *app;
} GuiWrapperObject;

static void GuiWrapper_dealloc(GuiWrapperObject *self) {
    Py_TYPE(self)->tp_free((PyObject *) self);
    delete self->controllerWrapper;
    delete self->mainLayout;
    delete self->app;
}

static PyObject *GuiWrapper_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    GuiWrapperObject *self;
    self = (GuiWrapperObject *) type->tp_alloc(type, 0);
    if (self != nullptr) {
        self->mainLayout = nullptr;
    }
    return (PyObject *) self;
}

static int GuiWrapper_init(GuiWrapperObject *self, PyObject *args, PyObject *kwds) {
    // get the first argument, should be a Controller
    PyObject *controller;
    if (!PyArg_ParseTuple(args, "O", &controller)) {
        return -1;
    }
    self->controllerWrapper = new ControllerWrapper(controller);

    int zero = 0; // hack to get QApplication to work
    self->app = new QApplication(zero, nullptr);
    self->mainLayout = new MainLayout(self->controllerWrapper);

    return 0;
}

static PyObject *GuiWrapper_run(GuiWrapperObject *self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    if (self->app == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "QApplication not initialized");
        return nullptr;
    }

    self->mainLayout->show();

    signal(SIGTERM, [](int) {
      qDebug() << "Received SIGTERM, quitting";
      QApplication::quit();
    });

    signal(SIGINT, [](int) {
      qDebug() << "Received SIGINT, quitting";
      QApplication::quit();
    });

    self->app->exec(); // long running
    return Py_None;
}

static PyObject *GuiWrapper_get_viewer_server_port(GuiWrapperObject *self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    return PyLong_FromLong(self->mainLayout->getViewerServerPort());
}

static PyObject *GuiWrapper_stop(GuiWrapperObject *self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    if (self->app == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "QApplication not initialized");
        return nullptr;
    }

    self->mainLayout->close();
    self->app->quit();
    return Py_None;
}

static PyMethodDef GuiWrapper_methods[] = {
        {"run", (PyCFunction) GuiWrapper_run, METH_NOARGS, "Starts the GUI event loop"},
        {"stop", (PyCFunction) GuiWrapper_stop, METH_NOARGS, "Stops the GUI event loop"},
        {"get_viewer_server_port", (PyCFunction) GuiWrapper_get_viewer_server_port, METH_NOARGS, "Returns the server port of the viewer"},
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

