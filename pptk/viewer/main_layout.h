#ifndef PPTK_MAIN_LAYOUT_H
#define PPTK_MAIN_LAYOUT_H

#include "ui_main_layout.h"
#include "viewer.h"
#include <QMainWindow>
#include <utility>


QT_BEGIN_NAMESPACE
namespace Ui {
  class MainLayout;
}
QT_END_NAMESPACE

class MainLayout : public QMainWindow {
  Q_OBJECT

  public:
  explicit MainLayout(int clientPort = 4001, std::function<void(std::string)> executeQueryCallback = ([](const auto& _){}), QWidget *parent = nullptr)
          : QMainWindow(parent), ui(new Ui::MainLayout), executeQueryCallback(std::move(executeQueryCallback)) {
    ui->setupUi(this);
    ui->statusbar->showMessage(tr("Loading..."));

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
  void on_executeQueryButton_clicked() {
    QString query = ui->queryTextBox->toPlainText();
    executeQueryCallback(query.toStdString());
    qDebug() << query;
  }

  private:
  Ui::MainLayout *ui;
  std::function<void(const std::string&)> executeQueryCallback;
};


#endif//PPTK_MAIN_LAYOUT_H
