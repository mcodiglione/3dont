#ifndef THREEDONT_GRAPH_TREE_MODEL_H
#define THREEDONT_GRAPH_TREE_MODEL_H

#include "../controller_wrapper.h"
#include "graph_tree_item.h"
#include <QAbstractItemModel>
#include <QApplication>
#include <QBrush>
#include <QColor>
#include <QFont>
#include <QPalette>
#include <QString>
#include <QVariant>
#include <QMultiHash>

class GraphTreeModel : public QAbstractItemModel {
  Q_OBJECT
public:
  explicit GraphTreeModel(ControllerWrapper *controllerWrapper, QObject *parent = nullptr);
  ~GraphTreeModel() override;

  [[nodiscard]] GraphTreeItem *itemFromIndex(const QModelIndex &index) const;
  [[nodiscard]] QModelIndex index(int row, int column, const QModelIndex &parent = QModelIndex()) const override;
  [[nodiscard]] QModelIndex parent(const QModelIndex &index) const override;
  [[nodiscard]] int rowCount(const QModelIndex &parent = QModelIndex()) const override;
  [[nodiscard]] int columnCount(const QModelIndex &parent = QModelIndex()) const override;
  [[nodiscard]] QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;
  [[nodiscard]] QVariant headerData(int section, Qt::Orientation orientation, int role = Qt::DisplayRole) const override;
  [[nodiscard]] bool canFetchMore(const QModelIndex &parent) const override;
  [[nodiscard]] bool hasChildren(const QModelIndex &parent) const override;
  [[nodiscard]] QModelIndex indexForItem(GraphTreeItem *item) const;
  void fetchMore(const QModelIndex &parent) override;
  bool removeRows(int row, int count, const QModelIndex &parent = QModelIndex()) override;

  void addTopLevelItem(const QString &object, const QString &predicate);
  void onChildrenLoaded(const QString &parentId, QStringList children);
  [[nodiscard]] QString getPredicate(const QModelIndex &index) const;
  [[nodiscard]] QString getObject(const QModelIndex &index) const;

public slots:
  void onRowExpanded(const QModelIndex &index);
  void onRowCollapsed(const QModelIndex &index);

private:
  GraphTreeItem *rootItem;
  ControllerWrapper *controllerWrapper;
  QMultiHash<QString, GraphTreeItem *> itemMap;
  QModelIndex highlightedIndex = QModelIndex();
};

#endif // THREEDONT_GRAPH_TREE_MODEL_H
