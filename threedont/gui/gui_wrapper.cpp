#include "controller_wrapper.h"
#include "main_layout.h"
#include "types.h"
#include <Python.h>
#include <QApplication>
#include <thread>
#include <signal.h>

typedef struct {
    PyObject_HEAD
    ControllerWrapper *controllerWrapper;
    MainLayout *mainLayout;
    QApplication *app;
    std::thread guiThread;

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
    // the first argument is a controller, the second the argv
    PyObject *controller, *argv;
    if (!PyArg_ParseTuple(args, "OO", &controller, &argv)) {
        PyErr_SetString(PyExc_TypeError, "GuiWrapper requires a controller and argv");
        return -1;
    }

    self->controllerWrapper = new ControllerWrapper(controller);
    // run the python stuff in a separate thread
    self->guiThread = std::thread([&self]() {self->controllerWrapper->start();});

    Py_ssize_t size = PyList_Size(argv);
    int* argc = new int(static_cast<int>(size + 1));  // +1 for program name

    // Allocate argv array on heap
    char** argvRaw = new char*[*argc];

    // Set argv[0] as program name
    const char* progName = "threedont";
    argvRaw[0] = new char[strlen(progName) + 1];
    std::strcpy(argvRaw[0], progName);

    // Fill in the rest from Python list
    for (Py_ssize_t i = 0; i < size; ++i) {
      PyObject* item = PyList_GetItem(argv, i);
      if (!PyUnicode_Check(item)) {
        PyErr_SetString(PyExc_TypeError, "argv must be a list of strings");
        return -1;
      }

      const char* arg = PyUnicode_AsUTF8(item);
      if (!arg) return -1;

      argvRaw[i + 1] = new char[strlen(arg) + 1];
      std::strcpy(argvRaw[i + 1], arg);
    }

    // This memory is intentionally leaked (it's fine if only done once)
    self->app = new QApplication(*argc, argvRaw);

    declareAllMetaTypes();

    self->mainLayout = new MainLayout(self->controllerWrapper);

    return 0;
}

static PyObject  *GuiWrapper_run(GuiWrapperObject *self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    auto stop = [](int sig) {
        qDebug() << "Received signal" << sig << ", quitting...";
        QApplication::quit();
    };
    signal(SIGINT, stop);
    signal(SIGTERM, stop);

    Py_BEGIN_ALLOW_THREADS
    qDebug() << "Starting GUI event loop";

    self->mainLayout->show();
    self->app->exec(); // long running

    self->guiThread.join();

    qDebug() << "GUI event loop exited";
    Py_END_ALLOW_THREADS

    return Py_None;
}

static PyObject *GuiWrapper_get_viewer_server_port(GuiWrapperObject *self, PyObject *args) {
    if (self->mainLayout == nullptr) {
      PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
      return nullptr;
    }

    return PyLong_FromLong(self->mainLayout->getViewerServerPort());
}

/**
 * This can be called safely from any thread
 * @param self
 * @param args
 * @return
 */
static PyObject *GuiWrapper_view_node_details(GuiWrapperObject* self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    // details are a list of tuples
    PyObject *details;
    const char* parentId;
    if (!PyArg_ParseTuple(args, "Os", &details, &parentId)) {
        return nullptr;
    }

    QVectorOfQStringPairs detailsVector;

    Py_ssize_t size = PyList_Size(details);
    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject *tuple = PyList_GetItem(details, i);
        if (!PyTuple_Check(tuple) || PyTuple_Size(tuple) != 2) {
            PyErr_SetString(PyExc_TypeError, "Details should be a list of tuples");
            return nullptr;
        }

        PyObject *key = PyTuple_GetItem(tuple, 0);
        PyObject *value = PyTuple_GetItem(tuple, 1);

        if (!PyUnicode_Check(key) || !PyUnicode_Check(value)) {
            PyErr_SetString(PyExc_TypeError, "Details should be a list of tuples of strings");
            return nullptr;
        }

        detailsVector.emplace_back(QString(PyUnicode_AsUTF8(key)), QString(PyUnicode_AsUTF8(value)));
    }

    QString parentIdString = QString(parentId);

    QMetaObject::invokeMethod(self->mainLayout, "displayNodeDetails", Qt::QueuedConnection, Q_ARG(QVectorOfQStringPairs, detailsVector), Q_ARG(QString, parentIdString));
    return Py_None;
}

static PyObject  *GuiWrapper_set_statusbar_content(GuiWrapperObject *self, PyObject *args) {
    if (self->mainLayout == nullptr) {
        PyErr_SetString(PyExc_RuntimeError, "MainLayout not initialized");
        return nullptr;
    }

    const char *content;
    int seconds;
    if (!PyArg_ParseTuple(args, "si", &content, &seconds)) {
        return nullptr;
    }

    QMetaObject::invokeMethod(self->mainLayout, "setStatusbarContent", Qt::QueuedConnection, Q_ARG(QString, QString(content)), Q_ARG(int, seconds));
    return Py_None;
}

static PyMethodDef GuiWrapper_methods[] = {
        {"run", (PyCFunction) GuiWrapper_run, METH_NOARGS, "Runs the GUI event loop"},
        {"set_statusbar_content", (PyCFunction) GuiWrapper_set_statusbar_content, METH_VARARGS, "Sets the content of the status bar"},
        {"get_viewer_server_port", (PyCFunction) GuiWrapper_get_viewer_server_port, METH_NOARGS, "Returns the server port of the viewer"},
        {"view_node_details", (PyCFunction) GuiWrapper_view_node_details, METH_VARARGS, "Displays the details of a point"},
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
        .m_base = PyModuleDef_HEAD_INIT,
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

