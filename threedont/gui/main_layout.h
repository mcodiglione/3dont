#ifndef THREEDONT_MAIN_LAYOUT_H
#define THREEDONT_MAIN_LAYOUT_H

#include "controller_wrapper.h"
#include "points_tree_view/graph_tree_model.h"
#include "ui_main_layout.h"
#include "viewer/viewer.h"
#include "widgets/scale_legend.h"
#include <QHeaderView>
#include <QInputDialog>
#include <QMainWindow>
#include <QTableWidget>
#include <QTreeView>

QT_BEGIN_NAMESPACE
namespace Ui {
  class MainLayout;
}
QT_END_NAMESPACE

class MainLayout : public QMainWindow {
  Q_OBJECT

public:
  explicit MainLayout(ControllerWrapper *controllerWrapper, QWidget *parent = nullptr);
  ~MainLayout() override;

  int getViewerServerPort();

protected:
  void closeEvent(QCloseEvent *event) override;
  bool eventFilter(QObject *obj, QEvent *event) override;

private slots:
  void cleanupOnExit();
  void singlePointSelected(unsigned int index);
  void setStatusbarContent(const QString &content, int seconds);
  void on_executeQueryButton_clicked();
  void on_actionCreate_project_triggered();
  void on_actionLegend_toggled(bool checked);
  void displayNodeDetails(const QStringList &details, const QString &parentId);
  void plotTabular(const QStringList &header, const QStringList &rows);
  void setQueryError(const QString &error);
  void setLegend(const QVariantList &colors, const QStringList &labels);
  void onTreeViewContexMenuRequested(const QPoint &pos);
  void detailsClosed(bool visible);
  void setProjectList(const QStringList &projects);

private:
  Ui::MainLayout *ui;
  Viewer *viewer;
  ControllerWrapper *controllerWrapper;
  GraphTreeModel *graphTreeModel;
  QDockWidget *legendDock = nullptr;
  bool isDetailsOpen = false;
  bool showLegend = true;
};

#endif // THREEDONT_MAIN_LAYOUT_H
