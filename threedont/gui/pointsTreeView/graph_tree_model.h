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
#include <utility>

class GraphTreeModel : public QAbstractItemModel {
  Q_OBJECT
public:
  explicit GraphTreeModel(ControllerWrapper *controllerWrapper, QObject *parent = nullptr)
      : QAbstractItemModel(parent), rootItem(new GraphTreeItem("", "")) {
    this->controllerWrapper = controllerWrapper;
  }

  ~GraphTreeModel() override {
    delete rootItem;
  }

  [[nodiscard]] GraphTreeItem *itemFromIndex(const QModelIndex &index) const {
    if (index.isValid())
      return static_cast<GraphTreeItem *>(index.internalPointer());
    return rootItem;// Fallback if index is invalid (e.g., the root)
  }

  [[nodiscard]] QModelIndex index(int row, int column, const QModelIndex &parent = QModelIndex()) const override {
    if (!hasIndex(row, column, parent)) {
      return {};
    }

    GraphTreeItem *parentItem;

    if (!parent.isValid()) {
      parentItem = rootItem;
    } else {
      parentItem = itemFromIndex(parent);
    }

    GraphTreeItem *childItem = parentItem->child(row);

    if (childItem) {
      return createIndex(row, column, childItem);
    } else {
      return {};
    }
  }

  [[nodiscard]] QModelIndex parent(const QModelIndex &index) const override {
    if (!index.isValid()) {
      return {};
    }

    GraphTreeItem *childItem = itemFromIndex(index);
    GraphTreeItem *parentItem = childItem->parent();

    if (parentItem == rootItem) {
      return {};
    }

    return createIndex(parentItem->childCount(), 0, parentItem);
  }

  [[nodiscard]] int rowCount(const QModelIndex &parent = QModelIndex()) const override {
    GraphTreeItem *parentItem;

    if (!parent.isValid())
      parentItem = rootItem;
    else
      parentItem = itemFromIndex(parent);


    return parentItem->childCount();
  }

  [[nodiscard]] int columnCount(const QModelIndex &parent = QModelIndex()) const override {
    if (parent.isValid())
      return itemFromIndex(parent)->columnCount();

    return rootItem->columnCount();
  }

  [[nodiscard]] QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override {
    if (!index.isValid())
      return {};

    GraphTreeItem *item = itemFromIndex(index);

    if (role == Qt::DisplayRole) {
      return item->data(index.column());
    } else if (role == Qt::FontRole && index == highlightedIndex) {
      QFont font;
      font.setBold(true);
      return font;
    } else if (role == Qt::ForegroundRole && index == highlightedIndex) {
      QColor highlightColor = qApp->palette().color(QPalette::HighlightedText);// HighlightedText
      return QBrush(highlightColor);
    }

    return {};
  }

  [[nodiscard]] QVariant headerData(int section, Qt::Orientation orientation, int role = Qt::DisplayRole) const override {
    if (role != Qt::DisplayRole)
      return {};

    if (orientation == Qt::Horizontal) {
      switch (section) {
        case 0:
          return QString("Predicate");
        case 1:
          return QString("Object");
        default:
          return {};
      }
    }
    return {};
  }

  [[nodiscard]] bool canFetchMore(const QModelIndex &parent) const override {
    if (!parent.isValid())
      return false;

    GraphTreeItem *item = itemFromIndex(parent);
    return !item->areChildrenLoaded() && !item->isLeaf();
  }

  [[nodiscard]] bool hasChildren(const QModelIndex &parent) const override {
    if (!parent.isValid())
      return true;

    GraphTreeItem *item = itemFromIndex(parent);
    return (item->areChildrenLoaded() && item->childCount() > 0) || !item->isLeaf();
  }

  QModelIndex indexForItem(GraphTreeItem *item) const {
    if (item == rootItem)
      return {};

    return createIndex(item->childIndex(), 0, item->parent());
  }

  void fetchMore(const QModelIndex &parent) override {
    if (!parent.isValid())
      return;

    auto *item = itemFromIndex(parent);

    if (item->areChildrenLoaded())
      return;

    QString nodeId = item->nodeId();

    controllerWrapper->viewNodeDetails(nodeId.toStdString());
  }

  bool removeRows(int row, int count, const QModelIndex &parent = QModelIndex()) override {
    if (!hasIndex(row, 0, parent))
      return false;

    beginRemoveRows(parent, row, row + count - 1);

    GraphTreeItem *parentItem = itemFromIndex(parent);
    for (int i = 0; i < count; ++i)
      parentItem->removeChild(row);

    endRemoveRows();
    return true;
  }

  void addTopLevelItem(const QString &object, const QString &predicate) {
    beginInsertRows(QModelIndex(), rootItem->childCount(), rootItem->childCount());
    auto *item = new GraphTreeItem(object, predicate, rootItem);
    itemMap.insert(item->nodeId(), item);// Store the mapping
    rootItem->appendChild(item);
    endInsertRows();
  }

  /**
     * @param parentId
     * @param children as flatten list of pairs
     */
  void onChildrenLoaded(const QString &parentId, QStringList children) {
    QList<GraphTreeItem *> parents;

    if (!itemMap.contains(parentId))
      addTopLevelItem(parentId, "");

    parents.append(itemMap.values(parentId));

    // all the items relatives to the same node in the graph, can be more than one
    for (const auto &item: parents) {
      if (item->areChildrenLoaded())
        continue;

      QModelIndex parentIndex = indexForItem(item);
      beginInsertRows(parentIndex, item->childCount(), item->childCount() + children.size() - 1);

      for (int i = 0; i < children.size(); i += 2) {
        auto *childItem = new GraphTreeItem(children[i + 1], children[i], item);
        itemMap.insert(childItem->nodeId(), childItem);// Store the mapping
        item->appendChild(childItem);
      }

      item->setChildrenLoaded(true);

      endInsertRows();
    }
  }

  [[nodiscard]] QString getPredicate(const QModelIndex &index) const {
    if (!index.isValid())
      return {};

    GraphTreeItem *item = itemFromIndex(index);
    return item->data(0, false).toString();
  }

  [[nodiscard]] QString getObject(const QModelIndex &index) const {
    if (!index.isValid())
      return {};

    GraphTreeItem *item = itemFromIndex(index);
    return item->data(1, false).toString();
  }

public slots:
  void onRowExpanded(const QModelIndex &index) {
    if (!index.isValid())
      return;

    GraphTreeItem *item = itemFromIndex(index);

    if (item->data(0) == "Constitutes")
      controllerWrapper->selectAllSubjects(item->data(0, false).toString().toStdString(),
                                           item->data(1, false).toString().toStdString());

    // highlightedIndex is the index of the column 1 that is expanded
    highlightedIndex = index.sibling(index.row(), 1);
    emit dataChanged(highlightedIndex, highlightedIndex, {Qt::FontRole});
  }

  void onRowCollapsed(const QModelIndex &index) {
    if (!index.isValid())
      return;

    QModelIndex siblingIndex = index.sibling(index.row(), 1);

    if (highlightedIndex == siblingIndex)
      highlightedIndex = QModelIndex();
    emit dataChanged(siblingIndex, siblingIndex, {Qt::FontRole});
  }

private:
  GraphTreeItem *rootItem;
  ControllerWrapper *controllerWrapper;
  QMultiHash<QString, GraphTreeItem *> itemMap;// Maps nodeId to GraphTreeItem
  QModelIndex highlightedIndex = QModelIndex();
};

#endif//THREEDONT_GRAPH_TREE_MODEL_H
