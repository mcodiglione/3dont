#ifndef THREEDONT_MAIN_LAYOUT_H
#define THREEDONT_MAIN_LAYOUT_H

#include "controller_wrapper.h"
#include "types.h"
#include "ui_main_layout.h"
#include "viewer/viewer.h"
#include "graph_tree_model.h"
#include <QHeaderView>
#include <QInputDialog>
#include <QMainWindow>
#include <QTableWidget>
#include <QTreeView>
#include <utility>


QT_BEGIN_NAMESPACE
namespace Ui {
  class MainLayout;
}
QT_END_NAMESPACE

class MainLayout : public QMainWindow {
  Q_OBJECT

  public:
  explicit MainLayout(ControllerWrapper* controllerWrapper, QWidget *parent = nullptr): QMainWindow(parent), ui(new Ui::MainLayout) {
    this->controllerWrapper = controllerWrapper;

    ui->setupUi(this);
    ui->statusbar->showMessage(tr("Loading..."));

    viewer = new Viewer();
    viewer->setFlags(Qt::FramelessWindowHint); // TODO is not enough
    QWidget *container = createWindowContainer(viewer, this);
    setCentralWidget(container);
    ui->statusbar->showMessage(tr("Ready"), 5000);

    connect(qApp, &QCoreApplication::aboutToQuit, this, &MainLayout::cleanupOnExit);
    connect(viewer, &Viewer::singlePointSelected, this, &MainLayout::singlePointSelected);
  }

  ~MainLayout() override {
    qDebug() << "Destroying main layout";
    delete ui;
  }

  int getViewerServerPort() {
    return viewer->getServerPort();
  }

  protected:
  void closeEvent(QCloseEvent *event) override {
    qDebug() << "Closing main layout";
    controllerWrapper->stop();
    event->accept();
  }

  private slots:
  void cleanupOnExit() {
    qDebug() << "Scheduling cleaning up main layout";
    this->deleteLater(); // schedule for deletion in the right thread
  }

  void singlePointSelected(unsigned int index) {
    controllerWrapper->viewPointDetails(index);
  }

  void setStatusbarContent(QString content, int seconds) {
    ui->statusbar->showMessage(content, seconds * 1000);
  }

  void on_executeSelectQueryButton_clicked() {
    QString query = ui->selectQueryTextBox->toPlainText();
    controllerWrapper->executeQuery(query.toStdString());
  }

  void on_actionConnect_to_server_triggered() {
    bool ok;
    QString dbUrl = QInputDialog::getText(this, tr("Connect to server"),
                                         tr("Server URL:"), QLineEdit::Normal,
                                         "http://localhost:8890/Nettuno", &ok);
    if (!ok || dbUrl.isEmpty())
      return;
    QString ontologyNamespace = QInputDialog::getText(this, tr("Connect to server"),
                                         tr("Ontology namespace:"), QLineEdit::Normal,
                                         "http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology", &ok);
    if (!ok || ontologyNamespace.isEmpty())
      return;

    controllerWrapper->connectToServer(dbUrl.toStdString(), ontologyNamespace.toStdString());
  }

  void displayNodeDetails(QVectorOfQStringPairs details, QString parentId) {
    qDebug() << "Displaying point details for " << parentId;

    if (!isDetailsOpen) {
      QDockWidget *dock = new QDockWidget(tr("Point details"), this);
      dock->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
      dock->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable | QDockWidget::DockWidgetClosable);
      // on dock close call detailsClosed
      connect(dock, &QDockWidget::visibilityChanged, this, &MainLayout::detailsClosed);

      graphTreeModel = new GraphTreeModel(controllerWrapper, this);
      QTreeView *treeView = new QTreeView(dock);
      treeView->setModel(graphTreeModel);

      dock->setWidget(treeView);

      isDetailsOpen = true;
      addDockWidget(Qt::LeftDockWidgetArea, dock);
    }

    graphTreeModel->onChildrenLoaded(std::move(parentId), std::move(details));

  }

  private:
  Ui::MainLayout *ui;
  Viewer *viewer;
  ControllerWrapper *controllerWrapper;
  GraphTreeModel *graphTreeModel;
  bool isDetailsOpen = false;

  private slots:
      void detailsClosed(bool visible) {
          if (visible)
              return;

          qDebug() << "Details closed";
          isDetailsOpen = false;
      }


};


#endif//THREEDONT_MAIN_LAYOUT_H
