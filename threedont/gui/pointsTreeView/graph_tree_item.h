#ifndef THREEDONT_GRAPH_TREE_ITEM_H
#define THREEDONT_GRAPH_TREE_ITEM_H

#include "../controller_wrapper.h"
#include <QAbstractItemModel>
#include <QApplication>
#include <QBrush>
#include <QColor>
#include <QFont>
#include <QPalette>
#include <QString>
#include <QVariant>
#include <utility>

class GraphTreeItem {
public:
  GraphTreeItem(QString object, QString predicate, GraphTreeItem *parent = nullptr)
      : predicate(std::move(predicate)), object(std::move(object)), parentItem(parent) {
  }

  ~GraphTreeItem() {
    qDeleteAll(childItems);
  }

  void appendChild(GraphTreeItem *child) {
    childItems.append(child);
  }

  GraphTreeItem *child(int row) {
    return childItems.value(row);
  }

  void removeChild(int row) {
    if (row >= 0 && row < childItems.size()) {
      delete childItems.takeAt(row);
    }
  }

  [[nodiscard]] int childCount() const {
    return childItems.count();
  }

  [[nodiscard]] int columnCount() const {
    return 2;// Name and Type
  }

  static QString removeNamespace(const QString &str) {
    int index = str.lastIndexOf('#');
    if (index != -1) {
      return str.mid(index + 1, str.length() - index - 2);
    }
    return str;
  }

  [[nodiscard]] QVariant data(int column, bool removeNS = true) const {
    QString out;
    if (column == 0)
      out = predicate;
    else if (column == 1)
      out = object;
    else
      return {};

    if (removeNS)
      out = removeNamespace(out);

    return out;
  }

  GraphTreeItem *parent() {
    return parentItem;
  }

  [[nodiscard]] bool areChildrenLoaded() const {
    return childrenLoaded;
  }

  void setChildrenLoaded(bool loaded) {
    childrenLoaded = loaded;
  }

  [[nodiscard]] QString nodeId() const {
    return object;
  }

  [[nodiscard]] int childIndex() const {
    if (parentItem) {
      return parentItem->childItems.indexOf(this);
    }
    return -1;
  }

  [[nodiscard]] bool isLeaf() const {
    return !object.startsWith("<http");// TODO is ugly
  }

private:
  QString predicate;
  QString object;
  GraphTreeItem *parentItem;
  QList<GraphTreeItem *> childItems;
  bool childrenLoaded = false;
};

#endif//THREEDONT_GRAPH_TREE_ITEM_H
