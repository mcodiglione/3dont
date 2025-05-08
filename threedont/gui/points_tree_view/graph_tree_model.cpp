#include "graph_tree_model.h"

GraphTreeModel::GraphTreeModel(ControllerWrapper *controllerWrapper, QObject *parent)
    : QAbstractItemModel(parent), rootItem(new GraphTreeItem("", "")) {
  this->controllerWrapper = controllerWrapper;
}

GraphTreeModel::~GraphTreeModel() {
  delete rootItem;
}

GraphTreeItem *GraphTreeModel::itemFromIndex(const QModelIndex &index) const {
  if (index.isValid())
    return static_cast<GraphTreeItem *>(index.internalPointer());
  return rootItem;
}

QModelIndex GraphTreeModel::index(int row, int column, const QModelIndex &parent) const {
  if (!hasIndex(row, column, parent)) return {};
  GraphTreeItem *parentItem = parent.isValid() ? itemFromIndex(parent) : rootItem;
  GraphTreeItem *childItem = parentItem->child(row);
  return childItem ? createIndex(row, column, childItem) : QModelIndex();
}

QModelIndex GraphTreeModel::parent(const QModelIndex &index) const {
  if (!index.isValid()) return {};
  GraphTreeItem *childItem = itemFromIndex(index);
  GraphTreeItem *parentItem = childItem->parent();
  if (parentItem == rootItem) return {};
  return createIndex(parentItem->childCount(), 0, parentItem);
}

int GraphTreeModel::rowCount(const QModelIndex &parent) const {
  GraphTreeItem *parentItem = parent.isValid() ? itemFromIndex(parent) : rootItem;
  return parentItem->childCount();
}

int GraphTreeModel::columnCount(const QModelIndex &parent) const {
  return parent.isValid() ? itemFromIndex(parent)->columnCount() : rootItem->columnCount();
}

QVariant GraphTreeModel::data(const QModelIndex &index, int role) const {
  if (!index.isValid()) return {};
  GraphTreeItem *item = itemFromIndex(index);
  if (role == Qt::DisplayRole) return item->data(index.column());
  if (role == Qt::FontRole && index == highlightedIndex) {
    QFont font;
    font.setBold(true);
    return font;
  }
  if (role == Qt::ForegroundRole && index == highlightedIndex) {
    QColor highlightColor = qApp->palette().color(QPalette::HighlightedText);
    return QBrush(highlightColor);
  }
  return {};
}

QVariant GraphTreeModel::headerData(int section, Qt::Orientation orientation, int role) const {
  if (role != Qt::DisplayRole || orientation != Qt::Horizontal) return {};
  switch (section) {
    case 0:
      return QString("Predicate");
    case 1:
      return QString("Object");
    default:
      return {};
  }
}

bool GraphTreeModel::canFetchMore(const QModelIndex &parent) const {
  if (!parent.isValid()) return false;
  GraphTreeItem *item = itemFromIndex(parent);
  return !item->areChildrenLoaded() && !item->isLeaf();
}

bool GraphTreeModel::hasChildren(const QModelIndex &parent) const {
  if (!parent.isValid()) return true;
  GraphTreeItem *item = itemFromIndex(parent);
  return (item->areChildrenLoaded() && item->childCount() > 0) || !item->isLeaf();
}

QModelIndex GraphTreeModel::indexForItem(GraphTreeItem *item) const {
  return item == rootItem ? QModelIndex() : createIndex(item->childIndex(), 0, item->parent());
}

void GraphTreeModel::fetchMore(const QModelIndex &parent) {
  if (!parent.isValid()) return;
  auto *item = itemFromIndex(parent);
  if (item->areChildrenLoaded()) return;
  controllerWrapper->viewNodeDetails(item->nodeId().toStdString());
}

bool GraphTreeModel::removeRows(int row, int count, const QModelIndex &parent) {
  if (!hasIndex(row, 0, parent)) return false;
  beginRemoveRows(parent, row, row + count - 1);
  GraphTreeItem *parentItem = itemFromIndex(parent);
  for (int i = 0; i < count; ++i)
    parentItem->removeChild(row);
  endRemoveRows();
  return true;
}

void GraphTreeModel::addTopLevelItem(const QString &object, const QString &predicate) {
  beginInsertRows(QModelIndex(), rootItem->childCount(), rootItem->childCount());
  auto *item = new GraphTreeItem(object, predicate, rootItem);
  itemMap.insert(item->nodeId(), item);
  rootItem->appendChild(item);
  endInsertRows();
}

void GraphTreeModel::onChildrenLoaded(const QString &parentId, QStringList children) {
  QList<GraphTreeItem *> parents;

  if (!itemMap.contains(parentId))
    addTopLevelItem(parentId, "");

  parents.append(itemMap.values(parentId));

  for (const auto &item: parents) {
    if (item->areChildrenLoaded())
      continue;

    QModelIndex parentIndex = indexForItem(item);
    beginInsertRows(parentIndex, item->childCount(), item->childCount() + children.size() / 2 - 1);

    for (int i = 0; i < children.size(); i += 2) {
      auto *childItem = new GraphTreeItem(children[i + 1], children[i], item);
      itemMap.insert(childItem->nodeId(), childItem);
      item->appendChild(childItem);
    }

    item->setChildrenLoaded(true);
    endInsertRows();
  }
}

QString GraphTreeModel::getPredicate(const QModelIndex &index) const {
  if (!index.isValid()) return {};
  return itemFromIndex(index)->data(0, false).toString();
}

QString GraphTreeModel::getObject(const QModelIndex &index) const {
  if (!index.isValid()) return {};
  return itemFromIndex(index)->data(1, false).toString();
}

void GraphTreeModel::onRowExpanded(const QModelIndex &index) {
  if (!index.isValid()) return;
  GraphTreeItem *item = itemFromIndex(index);

  if (item->data(0) == "Constitutes")
    controllerWrapper->selectAllSubjects(item->data(0, false).toString().toStdString(),
                                         item->data(1, false).toString().toStdString());

  highlightedIndex = index.sibling(index.row(), 1);
  emit dataChanged(highlightedIndex, highlightedIndex, {Qt::FontRole});
}

void GraphTreeModel::onRowCollapsed(const QModelIndex &index) {
  if (!index.isValid()) return;
  QModelIndex siblingIndex = index.sibling(index.row(), 1);
  if (highlightedIndex == siblingIndex)
    highlightedIndex = QModelIndex();
  emit dataChanged(siblingIndex, siblingIndex, {Qt::FontRole});
}
