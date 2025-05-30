#include "controller_wrapper.h"

void ControllerWrapper::callPythonMethod(PyObject *object, const char *methodName, const char *format, ...) {
  va_list args;
  va_start(args, format);
  PyGILState_STATE gil_state = PyGILState_Ensure(); // Acquire GIL

  PyObject *pyMethod = PyObject_GetAttrString(object, methodName);
  PyObject *result = nullptr;
  PyObject *pyArg = nullptr;

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
  PyGILState_Release(gil_state); // Release GIL
  va_end(args);
}

ControllerWrapper::ControllerWrapper(PyObject *controller) {
  for (const auto &method: neededMethods) {
    if (!PyObject_HasAttrString(controller, method.c_str())) {
      PyErr_SetString(PyExc_TypeError, "Controller must have all needed methods");
      throw std::invalid_argument("Controller must have all needed methods, missing: " + method);
    }
  }

  this->controller = controller;
  Py_XINCREF(controller);
}

ControllerWrapper::~ControllerWrapper() {
  Py_XDECREF(controller);
}

void ControllerWrapper::selectQuery(const std::string &query) {
  callPythonMethod(controller, "select_query", "s", query.c_str());
}

void ControllerWrapper::scalarQuery(const std::string &query) {
  callPythonMethod(controller, "scalar_query", "s", query.c_str());
}

void ControllerWrapper::connectToServer(const std::string &url, const std::string &ontologyNamespace) {
  callPythonMethod(controller, "connect_to_server", "ss", url.c_str(), ontologyNamespace.c_str());
}

void ControllerWrapper::stop() {
  callPythonMethod(controller, "stop", "");
}

void ControllerWrapper::viewPointDetails(unsigned int index) {
  callPythonMethod(controller, "view_point_details", "I", index);
}

void ControllerWrapper::viewNodeDetails(const std::string &node_id) {
  callPythonMethod(controller, "view_node_details", "s", node_id.c_str());
}

void ControllerWrapper::scalarWithPredicate(const std::string &predicate) {
  callPythonMethod(controller, "scalar_with_predicate", "s", predicate.c_str());
}

void ControllerWrapper::start() {
  callPythonMethod(controller, "start", "");
}

void ControllerWrapper::annotateNode(const std::string &subject, const std::string &predicate, const std::string &object) {
  callPythonMethod(controller, "annotate_node", "sss", subject.c_str(), predicate.c_str(), object.c_str());
}

void ControllerWrapper::selectAllSubjects(const std::string &predicate, const std::string &object) {
  callPythonMethod(controller, "select_all_subjects", "ss", predicate.c_str(), object.c_str());
}

void ControllerWrapper::tabularQuery(const std::string &query) {
  callPythonMethod(controller, "tabular_query", "s", query.c_str());
}

void ControllerWrapper::naturalLanguageQuery(const std::string &query) {
  callPythonMethod(controller, "natural_language_query", "s", query.c_str());
}
void ControllerWrapper::openProject(const std::string &projectName) {
  callPythonMethod(controller, "open_project", "s", projectName.c_str());
}
void ControllerWrapper::createProject(const std::string &projectName, const std::string &dbUrl, const std::string &graphUri, const std::string &ontologyNamespace) {
  callPythonMethod(controller, "create_project", "ssss", projectName.c_str(), dbUrl.c_str(), graphUri.c_str(), ontologyNamespace.c_str());
}
void ControllerWrapper::askProjectList() {
  callPythonMethod(controller, "get_project_list", "");
}
