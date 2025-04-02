#ifndef THREEDONT_MAIN_LAYOUT_H
#define THREEDONT_MAIN_LAYOUT_H

#include "controller_wrapper.h"
#include "types.h"
#include "ui_main_layout.h"
#include "viewer/viewer.h"
#include <QInputDialog>
#include <QMainWindow>
#include <QTableWidget>
#include <QHeaderView>
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
    viewer->setFlags(Qt::FramelessWindowHint);
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
    QString text = QInputDialog::getText(this, tr("Connect to server"),
                                         tr("Server URL:"), QLineEdit::Normal,
                                         "http://localhost:8890/Nettuno", &ok);
    if (ok && !text.isEmpty()) {
      controllerWrapper->connectToServer(text.toStdString());
    }
  }

  void displayPointDetails(QVectorOfQStringPairs details) {
    qDebug() << "Displaying point details";

    QDockWidget *dock = new QDockWidget(tr("Point details"), this);
    dock->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
    dock->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable | QDockWidget::DockWidgetClosable);
    QTableWidget *table = new QTableWidget(details.size(), 2, dock);
    dock->setWidget(table);

    int row = 0;
    QFlags itemFlags = Qt::ItemIsSelectable | Qt::ItemIsEnabled;
    for (const auto &pair : details) {
      table->setItem(row, 0, new QTableWidgetItem(pair.first));
      table->setItem(row, 1, new QTableWidgetItem(pair.second));
      table->item(row, 0)->setFlags(itemFlags);
      table->item(row, 1)->setFlags(itemFlags);
      row++;
    }

    table->verticalHeader()->hide();
    QStringList headerLabels;
    headerLabels << "Predicate" << "Object";
    table->setHorizontalHeaderLabels(headerLabels);

    addDockWidget(Qt::LeftDockWidgetArea, dock);
  }

  private:
  Ui::MainLayout *ui;
  Viewer *viewer;
  ControllerWrapper *controllerWrapper;
};


#endif//THREEDONT_MAIN_LAYOUT_H
