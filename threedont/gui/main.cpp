#include "main_layout.h"
#include <QApplication>
#include <QDebug>
#include <iostream>

int main(int argc, char *argv[]) {

  QApplication a(argc, argv);

  auto *mainWidget = new MainLayout(nullptr);
  mainWidget->show();

  return QApplication::exec();
}