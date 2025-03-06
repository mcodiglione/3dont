#ifndef THREEDONT_CONTROLLER_WRAPPER_H
#define THREEDONT_CONTROLLER_WRAPPER_H

#include <Python.h>
#include <string>
#include <stdexcept>

class ControllerWrapper {
  private:
    PyObject *controller;
    inline static std::string neededMethods[] = {
            "execute_query",
            "connect_to_server",
    };

  public:
      explicit ControllerWrapper(PyObject *controller) {
        for(const auto &method : neededMethods) {
          if (!PyObject_HasAttrString(controller, method.c_str())) {
            PyErr_SetString(PyExc_TypeError, "Controller must have all needed methods");
            throw std::invalid_argument("Controller must have all needed methods, missing: " + method);
          }
        }

        this->controller = controller;
        Py_XINCREF(controller);
      }

      ~ControllerWrapper() {
        Py_XDECREF(controller);
      }

      void executeQuery(const std::string &query) {
        PyObject *result = PyObject_CallMethod(controller, "execute_query", "s", query.c_str());
        Py_XDECREF(result);
      }

      void connectToServer(const std::string& url) {
        PyObject *result = PyObject_CallMethod(controller, "connect_to_server", "s", url.c_str());
        Py_XDECREF(result);
      }
};

#endif//THREEDONT_CONTROLLER_WRAPPER_H
