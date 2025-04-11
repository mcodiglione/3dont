#ifndef THREEDONT_CONTROLLER_WRAPPER_H
#define THREEDONT_CONTROLLER_WRAPPER_H

#include <Python.h>
#include <stdexcept>
#include <string>

class ControllerWrapper {
  private:
    PyObject *controller;
    inline static std::string neededMethods[] = {
            "execute_query",
            "connect_to_server",
            "stop"
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
        PyGILState_STATE gil_state = PyGILState_Ensure();
        PyObject *result = PyObject_CallMethod(controller, "execute_query", "s", query.c_str());
        Py_XDECREF(result);
        PyGILState_Release(gil_state);
      }

      void connectToServer(const std::string& url) {
        PyGILState_STATE gil_state = PyGILState_Ensure();
        PyObject *result = PyObject_CallMethod(controller, "connect_to_server", "s", url.c_str());
        Py_XDECREF(result);
        PyGILState_Release(gil_state);
      }

      void stop() {
        PyGILState_STATE gil_state = PyGILState_Ensure();
        PyObject *result = PyObject_CallMethod(controller, "stop", nullptr);
        Py_XDECREF(result);
        PyGILState_Release(gil_state);
      }

      void viewPointDetails(unsigned int index) {
        PyGILState_STATE gil_state = PyGILState_Ensure();
        PyObject *result = PyObject_CallMethod(controller, "view_point_details", "I", index);
        Py_XDECREF(result);
        PyGILState_Release(gil_state);
      }

      void viewNodeDetails(const std::string &node_id) {
        PyGILState_STATE gil_state = PyGILState_Ensure();
        PyObject *result = PyObject_CallMethod(controller, "view_node_details", "s", node_id.c_str());
        Py_XDECREF(result);
        PyGILState_Release(gil_state);
      }
};

#endif//THREEDONT_CONTROLLER_WRAPPER_H
