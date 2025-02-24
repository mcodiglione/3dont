#include <QApplication>
#include <QDebug>
#include <iostream>
#include "main_layout.h"

int main(int argc, char* argv[]) {
  if (argc != 2) {
    qDebug() << "usage: viewer <port number>";
    return 1;
  }

  QApplication a(argc, argv);

  auto clientPort = (unsigned short)atoi(argv[1]);
  auto *mainWidget = new MainLayout(clientPort);
  mainWidget->show();

  return QApplication::exec();
}