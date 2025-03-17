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

    ui->setupUi(this);
    ui->statusbar->showMessage(tr("Loading..."));

    viewer = new Viewer();
    viewer->setFlags(Qt::FramelessWindowHint);
    QWidget *container = createWindowContainer(viewer, this);
    setCentralWidget(container);
    ui->statusbar->showMessage(tr("Ready"), 5000);
  }

  ~MainLayout() override {
    delete ui;
  }

  int getViewerServerPort() {
    return viewer->getServerPort();
  }

  private slots:
  void on_executeQueryButton_clicked() {
    QString query = ui->queryTextBox->toPlainText();
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

  private:
  Ui::MainLayout *ui;
  Viewer *viewer;
  ControllerWrapper *controllerWrapper;
};


#endif//THREEDONT_MAIN_LAYOUT_H
