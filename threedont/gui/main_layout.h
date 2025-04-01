#ifndef THREEDONT_MAIN_LAYOUT_H
#define THREEDONT_MAIN_LAYOUT_H

#include "controller_wrapper.h"
#include "ui_main_layout.h"
#include "viewer/viewer.h"
#include <QMainWindow>
#include <QInputDialog>
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

    connect(qApp, &QCoreApplication::aboutToQuit, this, &MainLayout::cleanupOnExit);

    ui->setupUi(this);
    ui->statusbar->showMessage(tr("Loading..."));

    viewer = new Viewer();
    viewer->setFlags(Qt::FramelessWindowHint);
    QWidget *container = createWindowContainer(viewer, this);
    setCentralWidget(container);
    ui->statusbar->showMessage(tr("Ready"), 5000);
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

  void setStatusbarContent(QString content) {
    qDebug() << "Updating status bar content";
    qDebug() << content;

    ui->statusbar->showMessage(content, 5000);
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

  void displayPointDetails(QString data) {
    ui->statusbar->showMessage(data, 5000);
  }

  private:
  Ui::MainLayout *ui;
  Viewer *viewer;
  ControllerWrapper *controllerWrapper;
};


#endif//THREEDONT_MAIN_LAYOUT_H
