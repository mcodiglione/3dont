#ifndef THREEDONT_CONTROLLER_WRAPPER_H
#define THREEDONT_CONTROLLER_WRAPPER_H

#include <Python.h>
#include <cstdarg>
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
          "tabular_query",
          "configure_AWS_connection",
          "add_sensor",
          "update_sensors_and_reason",
          "provisional_set_args"};

  static void callPythonMethod(PyObject *object, const char *methodName, const char *format, ...);

public:
  explicit ControllerWrapper(PyObject *controller);
  ~ControllerWrapper();

  void selectQuery(const std::string &query);
  void scalarQuery(const std::string &query);
  void connectToServer(const std::string &url);
  void stop();
  void viewPointDetails(unsigned int index);
  void viewNodeDetails(const std::string &node_id);
  void scalarWithPredicate(const std::string &predicate);
  void start();
  void annotateNode(const std::string &subject, const std::string &predicate, const std::string &object);
  void selectAllSubjects(const std::string &predicate, const std::string &object);
  void tabularQuery(const std::string &query);
  void naturalLanguageQuery(const std::string &query);
  void configureAWSConnection(const std::string &access_key_id, const std::string &secret_access_key, const std::string &region, const std::string &profile_name);
  void addSensor(const std::string &sensor_name, const std::string &object_name, const std::string &property_name, const std::string &cert_pem_path, const std::string &private_key_path, const std::string &root_ca_path, const std::string &mqtt_topic, const std::string &client_id,);
  void updateSensorsAndReason();
  void provisionalSetArgs(const std::string &graph_uri, const std::string &ont_path, const std::string &pop_ont_path, const std::string &namespace, const std::string &populated_namespace, const std::string &virtuoso_isql);

};

#endif // THREEDONT_CONTROLLER_WRAPPER_H