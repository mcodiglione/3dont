#ifndef THREEDONT_MAIN_LAYOUT_H
#define THREEDONT_MAIN_LAYOUT_H

#include "controller_wrapper.h"
#include "pointsTreeView/graph_tree_model.h"
#include "scale_legend.h"
#include "ui_main_layout.h"
#include "viewer/viewer.h"
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
  explicit MainLayout(ControllerWrapper *controllerWrapper, QWidget *parent = nullptr) : QMainWindow(parent), ui(new Ui::MainLayout) {
    this->controllerWrapper = controllerWrapper;

    ui->setupUi(this);
    ui->errorLabel->setVisible(false);
    ui->statusbar->showMessage(tr("Loading..."));

    viewer = new Viewer();
    viewer->setFlags(Qt::FramelessWindowHint);// TODO is not enough
    // viewer->installEventFilter(this); TOTO fix focus issue
    QWidget *container = createWindowContainer(viewer, this);
    container->setFocusPolicy(Qt::StrongFocus);
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

  // fix focus issue on viewer
  bool eventFilter(QObject *obj, QEvent *event) override {
    if (event->type() == QEvent::MouseButtonPress) {
      ui->centralwidget->setFocus();
      viewer->requestActivate();
      return true;
    }
    return QObject::eventFilter(obj, event);
  }

private slots:
  void cleanupOnExit() {
    qDebug() << "Scheduling cleaning up main layout";
    this->deleteLater();// schedule for deletion in the right thread
  }

  void singlePointSelected(unsigned int index) {
    controllerWrapper->viewPointDetails(index);
  }

  void setStatusbarContent(const QString &content, int seconds) {
    ui->statusbar->showMessage(content, seconds * 1000);
  }

  void on_executeQueryButton_clicked() {
    QString queryType = ui->queryType->currentText();
    QString query = ui->queryTextBox->toPlainText();
    ui->errorLabel->setVisible(false);

    if (query.isEmpty())
      return;

    if (queryType == "select") {
      controllerWrapper->selectQuery(query.toStdString());
    } else if (queryType == "scalar") {
      controllerWrapper->scalarQuery(query.toStdString());
    } else if (queryType == "natural language") {
      controllerWrapper->naturalLanguageQuery(query.toStdString());
    } else if (queryType == "tabular") {
      controllerWrapper->tabularQuery(query.toStdString());
    } else {
      // should not happen
      ui->errorLabel->setText("Unknown query type");
      ui->errorLabel->setVisible(true);
    }
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

  void on_actionLegend_toggled(bool checked) {
    showLegend = checked;
    if (!checked && legendDock) {
      legendDock->close();
      legendDock = nullptr;
    }
  }

  void displayNodeDetails(const QStringList &details, const QString &parentId) {
    qDebug() << "Displaying node details for " << parentId;

    if (!isDetailsOpen) {
      QDockWidget *dock = new QDockWidget(tr("Point details"), this);
      dock->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
      dock->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable | QDockWidget::DockWidgetClosable);
      // on dock close call detailsClosed
      connect(dock, &QDockWidget::visibilityChanged, this, &MainLayout::detailsClosed);

      graphTreeModel = new GraphTreeModel(controllerWrapper, this);
      QTreeView *treeView = new QTreeView(dock);
      treeView->setContextMenuPolicy(Qt::CustomContextMenu);
      connect(treeView, &QTreeView::customContextMenuRequested, this, &MainLayout::onTreeViewContexMenuRequested);
      connect(treeView, &QTreeView::expanded, graphTreeModel, &GraphTreeModel::onRowExpanded);
      connect(treeView, &QTreeView::collapsed, graphTreeModel, &GraphTreeModel::onRowCollapsed);

      treeView->setModel(graphTreeModel);

      dock->setWidget(treeView);

      isDetailsOpen = true;
      addDockWidget(Qt::LeftDockWidgetArea, dock);
    }

    graphTreeModel->onChildrenLoaded(std::move(parentId), std::move(details));
  }

  void plotTabular(const QStringList &header, const QStringList &rows) {
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

  void setQueryError(const QString &error) {
    ui->errorLabel->setText(error);
    ui->errorLabel->setVisible(true);
  }

  void setLegend(const QVariantList &colors, const QStringList &labels) {
    if (!showLegend)
      return;

    if (legendDock)
      legendDock->close();

    QDockWidget *dock = new QDockWidget(tr("Legend"), this);
    dock->setAllowedAreas(Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea | Qt::BottomDockWidgetArea);
    dock->setFeatures(QDockWidget::DockWidgetMovable | QDockWidget::DockWidgetFloatable | QDockWidget::DockWidgetClosable);

    QList<QColor> colorList;
    for (const auto &color: colors) {
      //if (color.canConvert<QColor>()) { // TODO
      //colorList.append(color.value<QColor>());
      //} else
      if (color.canConvert<QString>()) {
        colorList.append(QColor(color.toString()));
      }
    }
    auto *legend = new ColorScaleLegend(colorList, labels, dock);
    dock->setWidget(legend);

    addDockWidget(Qt::BottomDockWidgetArea, dock);
    legendDock = dock;
  }

  void onTreeViewContexMenuRequested(const QPoint &pos) {
    QTreeView *treeView = qobject_cast<QTreeView *>(sender());
    if (!treeView)
      return;

    QModelIndex index = treeView->indexAt(pos);
    if (!index.isValid())
      return;

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
      QString predicate = QInputDialog::getText(this, tr("Annotate"),
                                                tr("Predicate:"), QLineEdit::Normal,
                                                "http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#", &ok);
      if (!ok || predicate.isEmpty())
        return;
      QString newObject = QInputDialog::getText(this, tr("Annotate"), tr("Object:"), QLineEdit::Normal,
                                                "http://www.semanticweb.org/mcodi/ontologies/2024/3/Urban_Ontology#", &ok);
      if (!ok || newObject.isEmpty())
        return;
      controllerWrapper->annotateNode(subject.toStdString(), predicate.toStdString(), newObject.toStdString());
    });
    QAction *selectAll = contextMenu.addAction("Select all");
    connect(selectAll, &QAction::triggered, [this, predicate, object]() {
      controllerWrapper->selectAllSubjects(predicate.toStdString(), object.toStdString());
    });

    // if it's a top level item, show a "remove item" action
    if (!index.parent().isValid()) {
      QAction *removeAction = contextMenu.addAction("Remove item");
      connect(removeAction, &QAction::triggered, [this, index]() {
        graphTreeModel->removeRow(index.row(), index.parent());
      });
    }

    contextMenu.exec(treeView->viewport()->mapToGlobal(pos));
  }

  void detailsClosed(bool visible) {
    if (visible)
      return;

    qDebug() << "Details closed";
    isDetailsOpen = false;
  }

private:
  Ui::MainLayout *ui;
  Viewer *viewer;
  ControllerWrapper *controllerWrapper;
  GraphTreeModel *graphTreeModel;
  QDockWidget *legendDock = nullptr;
  bool isDetailsOpen = false;
  bool showLegend = true;
};

#endif//THREEDONT_MAIN_LAYOUT_H
