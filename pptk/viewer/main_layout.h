#ifndef PPTK_MAIN_LAYOUT_H
#define PPTK_MAIN_LAYOUT_H

#include "ui_main_layout.h"
#include "viewer.h"
#include <QMainWindow>


QT_BEGIN_NAMESPACE
namespace Ui {
  class MainLayout;
}
QT_END_NAMESPACE

class MainLayout : public QMainWindow {
  Q_OBJECT

  public:
  explicit MainLayout(int clientPort = 4001, QWidget *parent = nullptr) : QMainWindow(parent), ui(new Ui::MainLayout) {
    ui->setupUi(this);
    ui->statusbar->showMessage(tr("Loading..."));

    connect(ui->executeQueryButton, SIGNAL(clicked()), this, SLOT(on_pushButton_clicked()));

    QWindow *viewer = new Viewer(clientPort);
    viewer->setFlags(Qt::FramelessWindowHint);
    QWidget *container = createWindowContainer(viewer, this);
    setCentralWidget(container);
    ui->statusbar->showMessage(tr("Ready"), 5000);
  }

  ~MainLayout() override {
    delete ui;
  }

  private slots:
  void on_pushButton_clicked() {
    QString query = ui->queryTextBox->toPlainText();
    qDebug() << query;
  }

  private:
  Ui::MainLayout *ui;
};


#endif//PPTK_MAIN_LAYOUT_H
