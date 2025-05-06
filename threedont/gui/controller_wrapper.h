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
          "natural_language_query",
          "tabular_query"};

  static void callPythonMethod(PyObject *object, const char *methodName, const char *format, ...) {
    va_list args;
    va_start(args, format);
    PyGILState_STATE gil_state = PyGILState_Ensure();// Acquire GIL

    PyObject *pyMethod = PyObject_GetAttrString(object, methodName);
    PyObject *result;
    PyObject *pyArg;
    switch (strlen(format)) {
      case 0:
        result = PyObject_CallNoArgs(pyMethod);
        break;
      case 1:
        pyArg = Py_VaBuildValue(format, args);
        result = PyObject_CallOneArg(pyMethod, pyArg);
        Py_XDECREF(pyArg);
        break;
      default:
        pyArg = Py_VaBuildValue(format, args);
        result = PyObject_CallObject(pyMethod, pyArg);
        Py_XDECREF(pyArg);
    }
    Py_XDECREF(pyMethod);
    Py_XDECREF(result);

    PyGILState_Release(gil_state);// Release GIL
    va_end(args);
  }


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
    callPythonMethod(controller, "select_query", "s", query.c_str());
  }

  void scalarQuery(const std::string &query) {
    callPythonMethod(controller, "scalar_query", "s", query.c_str());
  }

  void connectToServer(const std::string &url, const std::string &ontologyNamespace) {
    callPythonMethod(controller, "connect_to_server", "ss", url.c_str(), ontologyNamespace.c_str());
  }

  void stop() {
    callPythonMethod(controller, "stop", "");
  }

  void viewPointDetails(unsigned int index) {
    callPythonMethod(controller, "view_point_details", "I", index);
  }

  void viewNodeDetails(const std::string &node_id) {
    callPythonMethod(controller, "view_node_details", "s", node_id.c_str());
  }

  void scalarWithPredicate(const std::string &predicate) {
    callPythonMethod(controller, "scalar_with_predicate", "s", predicate.c_str());
  }

  void start() {
    callPythonMethod(controller, "start", "");
  }

  void annotateNode(const std::string &subject, const std::string &predicate, const std::string &object) {
    callPythonMethod(controller, "annotate_node", "sss", subject.c_str(), predicate.c_str(), object.c_str());
  }

  void selectAllSubjects(const std::string &predicate, const std::string &object) {
    callPythonMethod(controller, "select_all_subjects", "ss", predicate.c_str(), object.c_str());
  }

  void tabularQuery(const std::string &query) {
    callPythonMethod(controller, "tabular_query", "s", query.c_str());
  }

  void naturalLanguageQuery(const std::string &query) {
    callPythonMethod(controller, "natural_language_query", "s", query.c_str());
  }
};

#endif//THREEDONT_CONTROLLER_WRAPPER_H
