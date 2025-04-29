#ifndef THREEDONT_CONTROLLER_WRAPPER_H
#define THREEDONT_CONTROLLER_WRAPPER_H

#include <Python.h>
#include <stdexcept>
#include <string>

class ControllerWrapper {
  private:
  PyObject *controller;
  inline static std::string neededMethods[] = {
          "select_query",
          "scalar_query",
          "connect_to_server",
          "stop",
          "view_point_details",
          "view_node_details",
          "start",
          "annotate_node",
          "select_all_subjects",
          "tabular_query"};

  public:
  explicit ControllerWrapper(PyObject *controller) {
    for (const auto &method: neededMethods) {
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

  void selectQuery(const std::string &query) {
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(controller, "select_query", "s", query.c_str());
    Py_XDECREF(result);
    PyGILState_Release(gil_state);
  }

  void scalarQuery(const std::string &query) {
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(controller, "scalar_query", "s", query.c_str());
    Py_XDECREF(result);
    PyGILState_Release(gil_state);
  }

  void connectToServer(const std::string &url, const std::string &ontologyNamespace) {
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(controller, "connect_to_server", "ss", url.c_str(), ontologyNamespace.c_str());
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

  void scalarWithPredicate(const std::string &predicate) {
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(controller, "scalar_with_predicate", "s", predicate.c_str());
    Py_XDECREF(result);
    PyGILState_Release(gil_state);
  }

  void start() {
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(controller, "start", nullptr);
    Py_XDECREF(result);
    PyGILState_Release(gil_state);
  }

  void annotateNode(const std::string &subject, const std::string &predicate, const std::string &object) {
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(controller, "annotate_node", "sss", subject.c_str(), predicate.c_str(), object.c_str());
    Py_XDECREF(result);
    PyGILState_Release(gil_state);
  }

  void selectAllSubjects(const std::string &predicate, const std::string &object) {
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(controller, "select_all_subjects", "ss", predicate.c_str(), object.c_str());
    Py_XDECREF(result);
    PyGILState_Release(gil_state);
  }

  void tabularQuery(const std::string &query) {
    PyGILState_STATE gil_state = PyGILState_Ensure();
    PyObject *result = PyObject_CallMethod(controller, "tabular_query", "s", query.c_str());
    Py_XDECREF(result);
    PyGILState_Release(gil_state);
  }
};

#endif//THREEDONT_CONTROLLER_WRAPPER_H
