#include "controller_wrapper.h"
#include "main_layout.h"
#include <Python.h>
#include <QApplication>
#include <iostream>
#include <thread>
#include <mutex>

typedef struct {
    PyObject_HEAD
    ControllerWrapper *controllerWrapper;
    MainLayout *mainLayout;
    QApplication *app;
    std::thread guiThread;
    std::mutex initLock;

} GuiWrapperObject;

static void GuiWrapper_dealloc(GuiWrapperObject *self) {
    // qt handles the deletion of the main layout and the app
    delete self->controllerWrapper;
    Py_TYPE(self)->tp_free((PyObject *) self);
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
    self->initLock.lock();

    auto runApp = [self]() {
      int zero = 0;
      self->app = new QApplication(zero, nullptr);

      self->mainLayout = new MainLayout(self->controllerWrapper);
      self->initLock.unlock(); // when the viewer is ready the port number will be available

      qDebug() << "Starting GUI event loop";

      self->mainLayout->show();
      self->app->exec(); // long running

      qDebug() << "GUI event loop exited";
    };

    self->guiThread = std::thread(runApp);

    return 0;
}

static PyObject *GuiWrapper_wait_init(GuiWrapperObject *self, PyObject *args) {
    std::lock_guard<std::mutex> lock(self->initLock);

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

    Py_BEGIN_ALLOW_THREADS

    qDebug() << "Stopping GUI event loop";
    QApplication::quit();

    qDebug() << "Waiting for GUI thread to finish";
    self->guiThread.join();

    qDebug() << "GUI stopped with stop() method";

    Py_END_ALLOW_THREADS

    return Py_None;
}

/**
 * This can be called safely from any thread
 * @param self
 * @param args
 * @return
 */
static PyObject *GuiWrapper_view_point_details(GuiWrapperObject* self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    QString data;
    if (!PyArg_ParseTuple(args, "s", &data)) {
        return nullptr;
    }

    QMetaObject::invokeMethod(self->mainLayout, "displayPointDetails", Qt::QueuedConnection, Q_ARG(QString, data));
    return Py_None;
}

static PyObject  *GuiWrapper_set_statusbar_content(GuiWrapperObject *self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    QString content;
    if (!PyArg_ParseTuple(args, "s", &content)) {
        return nullptr;
    }
    // TODO the string is always empty

    QMetaObject::invokeMethod(self->mainLayout, "setStatusbarContent", Qt::QueuedConnection, Q_ARG(QString, content));
    return Py_None;
}

static PyMethodDef GuiWrapper_methods[] = {
        {"set_statusbar_content", (PyCFunction) GuiWrapper_set_statusbar_content, METH_VARARGS, "Sets the content of the status bar"},
        {"stop", (PyCFunction) GuiWrapper_stop, METH_NOARGS, "Stops the GUI event loop"},
        {"wait_init", (PyCFunction) GuiWrapper_wait_init, METH_NOARGS, "Waits for the GUI to be initialized"},
        {"get_viewer_server_port", (PyCFunction) GuiWrapper_get_viewer_server_port, METH_NOARGS, "Returns the server port of the viewer"},
        {"view_point_details", (PyCFunction) GuiWrapper_view_point_details, METH_VARARGS, "Displays the details of a point"},
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

