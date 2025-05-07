#include "graph_tree_item.h"
#include <QRegularExpression>

GraphTreeItem::GraphTreeItem(QString object, QString predicate, GraphTreeItem *parent)
    : predicate(std::move(predicate)), object(std::move(object)), parentItem(parent) {}

GraphTreeItem::~GraphTreeItem() {
  qDeleteAll(childItems);
}

void GraphTreeItem::appendChild(GraphTreeItem *child) {
  childItems.append(child);
}

GraphTreeItem *GraphTreeItem::child(int row) {
  return childItems.value(row);
}

void GraphTreeItem::removeChild(int row) {
  if (row >= 0 && row < childItems.size())
    delete childItems.takeAt(row);
}

int GraphTreeItem::childCount() const {
  return childItems.count();
}

int GraphTreeItem::columnCount() const {
  return 2; // Predicate and Object
}

QVariant GraphTreeItem::data(int column, bool removeNS) const {
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

QString GraphTreeItem::removeNamespace(const QString &str) {
  int index = str.lastIndexOf('#');
  if (index != -1)
    return str.mid(index + 1, str.length() - index - 2); // assumes closing angle bracket
  return str;
}

GraphTreeItem *GraphTreeItem::parent() {
  return parentItem;
}

bool GraphTreeItem::areChildrenLoaded() const {
  return childrenLoaded;
}

void GraphTreeItem::setChildrenLoaded(bool loaded) {
  childrenLoaded = loaded;
}

QString GraphTreeItem::nodeId() const {
  return object;
}

int GraphTreeItem::childIndex() const {
  if (parentItem)
    return parentItem->childItems.indexOf(this);
  return -1;
}

bool GraphTreeItem::isLeaf() const {
  return !object.startsWith("<http"); // heuristic
}
