#include "main_layout.h"
#include <QAction>
#include <QDebug>
#include <QDockWidget>
#include <QLineEdit>
#include <QMenu>

MainLayout::MainLayout(ControllerWrapper *controllerWrapper, QWidget *parent)
    : QMainWindow(parent), ui(new Ui::MainLayout), controllerWrapper(controllerWrapper) {
  ui->setupUi(this);
  ui->errorLabel->setVisible(false);
  ui->statusbar->showMessage(tr("Loading..."));

  viewer = new Viewer();
  viewer->setFlags(Qt::FramelessWindowHint);
  QWidget *container = createWindowContainer(viewer, this);
  container->setFocusPolicy(Qt::StrongFocus);
  setCentralWidget(container);
  ui->statusbar->showMessage(tr("Ready"), 5000);

  connect(qApp, &QCoreApplication::aboutToQuit, this, &MainLayout::cleanupOnExit);
  connect(viewer, &Viewer::singlePointSelected, this, &MainLayout::singlePointSelected);
}

MainLayout::~MainLayout() {
  qDebug() << "Destroying main layout";
  delete ui;
}

int MainLayout::getViewerServerPort() {
  return viewer->getServerPort();
}

void MainLayout::closeEvent(QCloseEvent *event) {
  qDebug() << "Closing main layout";
  controllerWrapper->stop();
  event->accept();
}

bool MainLayout::eventFilter(QObject *obj, QEvent *event) {
  if (event->type() == QEvent::MouseButtonPress) {
    ui->centralwidget->setFocus();
    viewer->requestActivate();
    return true;
  }
  return QObject::eventFilter(obj, event);
}

void MainLayout::cleanupOnExit() {
  qDebug() << "Scheduling cleaning up main layout";
  this->deleteLater();
}

void MainLayout::singlePointSelected(unsigned int index) {
  controllerWrapper->viewPointDetails(index);
}

void MainLayout::setStatusbarContent(const QString &content, int seconds) {
  ui->statusbar->showMessage(content, seconds * 1000);
}

void MainLayout::on_executeQueryButton_clicked() {
  QString queryType = ui->queryType->currentText();
  QString query = ui->queryTextBox->toPlainText();
  ui->errorLabel->setVisible(false);

  if (query.isEmpty()) return;

  if (queryType == "select") {
    controllerWrapper->selectQuery(query.toStdString());
  } else if (queryType == "scalar") {
    controllerWrapper->scalarQuery(query.toStdString());
  } else if (queryType == "natural language") {
    controllerWrapper->naturalLanguageQuery(query.toStdString());
  } else if (queryType == "tabular") {
    controllerWrapper->tabularQuery(query.toStdString());
  } else {
    ui->errorLabel->setText("Unknown query type");
    ui->errorLabel->setVisible(true);
  }
}

void MainLayout::on_actionConnect_to_server_triggered() {
  bool ok;
  QString dbUrl = QInputDialog::getText(this, tr("Connect to server"), tr("Server URL:"),
                                        QLineEdit::Normal, "http://localhost:8890/Nettuno", &ok);
  if (!ok || dbUrl.isEmpty()) return;

  QString ontologyNamespace = QInputDialog::getText(this, tr("Connect to server"), tr("Ontology namespace:"),
                                                    QLineEdit::Normal, "http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology", &ok);
  if (!ok || ontologyNamespace.isEmpty()) return;

  controllerWrapper->connectToServer(dbUrl.toStdString(), ontologyNamespace.toStdString());
}

void MainLayout::on_actionLegend_toggled(bool checked) {
  showLegend = checked;
  if (!checked && legendDock) {
    legendDock->close();
    legendDock = nullptr;
  }
}

void MainLayout::displayNodeDetails(const QStringList &details, const QString &parentId) {
  qDebug() << "Displaying node details for " << parentId;

  if (!isDetailsOpen) {
    QDockWidget *dock = new QDockWidget(tr("Point details"), this);
    dock->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
    dock->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable | QDockWidget::DockWidgetClosable);
    connect(dock, &QDockWidget::visibilityChanged, this, &MainLayout::detailsClosed);

    graphTreeModel = new GraphTreeModel(controllerWrapper, this);
    QTreeView *treeView = new QTreeView(dock);
    treeView->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(treeView, &QTreeView::customContextMenuRequested, this, &MainLayout::onTreeViewContexMenuRequested);
    connect(treeView, &QTreeView::expanded, graphTreeModel, &GraphTreeModel::onRowExpanded);
    connect(treeView, &QTreeView::collapsed, graphTreeModel, &GraphTreeModel::onRowCollapsed);
    treeView->setModel(graphTreeModel);
    dock->setWidget(treeView);
    addDockWidget(Qt::LeftDockWidgetArea, dock);
    isDetailsOpen = true;
  }

  graphTreeModel->onChildrenLoaded(parentId, details);
}

void MainLayout::plotTabular(const QStringList &header, const QStringList &rows) {
  auto dock = new QDockWidget(tr("Tabular data"), this);
  dock->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
  dock->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable | QDockWidget::DockWidgetClosable);

  int nVars = header.size();
  QTableWidget *tableWidget = new QTableWidget(dock);
  tableWidget->setColumnCount(nVars);
  tableWidget->setRowCount(rows.size() / nVars);
  tableWidget->setHorizontalHeaderLabels(header);
  tableWidget->verticalHeader()->setVisible(false);

  for (int i = 0; i < rows.size() / nVars; ++i) {
    for (int j = 0; j < nVars; ++j) {
      QTableWidgetItem *item = new QTableWidgetItem(rows[i * nVars + j]);
      tableWidget->setItem(i, j, item);
    }
  }

  dock->setWidget(tableWidget);
  addDockWidget(Qt::LeftDockWidgetArea, dock);
}

void MainLayout::setQueryError(const QString &error) {
  ui->errorLabel->setText(error);
  ui->errorLabel->setVisible(true);
}

void MainLayout::setLegend(const QVariantList &colors, const QStringList &labels) {
  if (!showLegend) return;
  if (legendDock) legendDock->close();

  QDockWidget *dock = new QDockWidget(tr("Legend"), this);
  dock->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea | Qt::BottomDockWidgetArea);
  dock->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable | QDockWidget::DockWidgetClosable);

  QList<QColor> colorList;
  for (const auto &color: colors)
    if (color.canConvert<QString>())
      colorList.append(QColor(color.toString()));

  auto *legend = new ColorScaleLegend(colorList, labels, dock);
  dock->setWidget(legend);
  addDockWidget(Qt::BottomDockWidgetArea, dock);
  legendDock = dock;
}

void MainLayout::onTreeViewContexMenuRequested(const QPoint &pos) {
  QTreeView *treeView = qobject_cast<QTreeView *>(sender());
  if (!treeView) return;

  QModelIndex index = treeView->indexAt(pos);
  if (!index.isValid()) return;

  QString predicate = graphTreeModel->getPredicate(index);
  QString object = graphTreeModel->getObject(index);

  QMenu contextMenu;
  QAction *plotAction = contextMenu.addAction("Plot predicate");
  connect(plotAction, &QAction::triggered, [this, predicate]() {
    controllerWrapper->scalarWithPredicate(predicate.toStdString());
  });

  QAction *annotate = contextMenu.addAction("Annotate");
  connect(annotate, &QAction::triggered, [this, object]() {
    QString subject = object;
    bool ok;
    QString predicate = QInputDialog::getText(this, tr("Annotate"), tr("Predicate:"), QLineEdit::Normal,
                                              "http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#", &ok);
    if (!ok || predicate.isEmpty()) return;
    QString newObject = QInputDialog::getText(this, tr("Annotate"), tr("Object:"), QLineEdit::Normal,
                                              "http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#", &ok);
    if (!ok || newObject.isEmpty()) return;

    controllerWrapper->annotateNode(subject.toStdString(), predicate.toStdString(), newObject.toStdString());
  });

  QAction *selectAll = contextMenu.addAction("Select all");
  connect(selectAll, &QAction::triggered, [this, predicate, object]() {
    controllerWrapper->selectAllSubjects(predicate.toStdString(), object.toStdString());
  });

  if (!index.parent().isValid()) {
    QAction *removeAction = contextMenu.addAction("Remove item");
    connect(removeAction, &QAction::triggered, [this, index]() {
      graphTreeModel->removeRow(index.row(), index.parent());
    });
  }

  contextMenu.exec(treeView->viewport()->mapToGlobal(pos));
}

void MainLayout::detailsClosed(bool visible) {
  if (visible) return;
  qDebug() << "Details closed";
  isDetailsOpen = false;
}


void MainLayout::setProjectList(const QStringList &projects) {
  // TODO
}
