#ifndef THREEDONT_GRAPH_TREE_MODEL_H
#define THREEDONT_GRAPH_TREE_MODEL_H

#include "controller_wrapper.h"
#include "types.h"
#include <QAbstractItemModel>
#include <QString>
#include <QVariant>

class GraphTreeItem {
public:
    GraphTreeItem(const QString &object, const QString &predicate, GraphTreeItem *parent = nullptr)
        : predicate(predicate), object(object), parentItem(parent) {
    }

    void appendChild(GraphTreeItem *child) {
        childItems.append(child);
    }

    GraphTreeItem *child(int row) {
        return childItems.value(row);
    }

    int childCount() const {
        return childItems.count();
    }

    int columnCount() const {
        return 2; // Name and Type
    }

    static QString removeNamespace(const QString &str) {
        int index = str.lastIndexOf('#');
        if (index != -1) {
          return str.mid(index + 1, str.length() - index - 2);
        }
        return str;
    }

    QVariant data(int column, bool removeNS = true) const {
        QString out;
        if (column == 0)
            out = predicate;
        else if (column == 1)
            out = object;
        else
          return QVariant();

        if (removeNS)
            out = removeNamespace(out);

        return out;
    }

    GraphTreeItem *parent() {
        return parentItem;
    }

    bool areChildrenLoaded() const {
        return childrenLoaded;
    }

    void setChildrenLoaded(bool loaded) {
        childrenLoaded = loaded;
    }

    QString nodeId() const {
        return object;
    }

    int childIndex() const {
        if (parentItem) {
            return parentItem->childItems.indexOf(this);
        }
        return -1;
    }

    bool isLeaf() const {
      return !object.startsWith("<http"); // TODO is ugly
    }


private:
    QString predicate;
    QString object;
    GraphTreeItem *parentItem;
    QList<GraphTreeItem *> childItems;
    bool childrenLoaded = false;
};

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

    QModelIndex index(int row, int column, const QModelIndex &parent = QModelIndex()) const override {
        if (!hasIndex(row, column, parent)) {
            return QModelIndex();
        }

        GraphTreeItem *parentItem;

        if (!parent.isValid()) {
            parentItem = rootItem;
        } else {
            parentItem = static_cast<GraphTreeItem *>(parent.internalPointer());
        }

        GraphTreeItem *childItem = parentItem->child(row);

        if (childItem) {
            return createIndex(row, column, childItem);
        } else {
            return QModelIndex();
        }
    }

    QModelIndex parent(const QModelIndex &index) const override {
        if (!index.isValid()) {
            return QModelIndex();
        }

        GraphTreeItem *childItem = static_cast<GraphTreeItem *>(index.internalPointer());
        GraphTreeItem *parentItem = childItem->parent();

        if (parentItem == rootItem) {
            return QModelIndex();
        }

        return createIndex(parentItem->childCount(), 0, parentItem);
    }

    int rowCount(const QModelIndex &parent = QModelIndex()) const override {
        GraphTreeItem *parentItem;

        if (!parent.isValid()) {
            parentItem = rootItem;
        } else {
            parentItem = static_cast<GraphTreeItem *>(parent.internalPointer());
        }

        return parentItem->childCount();
    }

    int columnCount(const QModelIndex &parent = QModelIndex()) const override {
        if (parent.isValid()) {
            return static_cast<GraphTreeItem *>(parent.internalPointer())->columnCount();
        }
        return rootItem->columnCount();
    }

    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override {
        if (!index.isValid() || role != Qt::DisplayRole) {
            return QVariant();
        }

        GraphTreeItem *item = static_cast<GraphTreeItem *>(index.internalPointer());

        return item->data(index.column());
    }

    QVariant headerData(int section, Qt::Orientation orientation, int role = Qt::DisplayRole) const override {
        if (role != Qt::DisplayRole) {
            return QVariant();
        }

        if (orientation == Qt::Horizontal) {
            switch (section) {
                case 0:
                    return QString("Predicate");
                case 1:
                    return QString("Object");
                default:
                    return QVariant();
            }
        }
        return QVariant();
    }

    bool canFetchMore(const QModelIndex &parent) const override {
        if (!parent.isValid()) {
            return false;
        }

        GraphTreeItem *item = static_cast<GraphTreeItem *>(parent.internalPointer());
        return !item->areChildrenLoaded() && !item->isLeaf();
    }

    bool hasChildren(const QModelIndex &parent) const override {
        if (!parent.isValid()) {
            return true;
        }

        GraphTreeItem *item = static_cast<GraphTreeItem *>(parent.internalPointer());
        return (item->areChildrenLoaded() && item->childCount() > 0) || !item->isLeaf();
    }

    QModelIndex indexForItem(GraphTreeItem* item) const {
        if (item == rootItem) {
            return QModelIndex();
        }

        return createIndex(item->childIndex(), 0, item->parent());
    }

    void fetchMore(const QModelIndex &parent) override {
        if (!parent.isValid())
            return;

        GraphTreeItem *item = static_cast<GraphTreeItem *>(parent.internalPointer());

        if (item->areChildrenLoaded())
            return;

        QString nodeId = item->nodeId();

        controllerWrapper->viewNodeDetails(nodeId.toStdString());
    }

    void addTopLevelItem(const QString &object, const QString &predicate) {
        beginInsertRows(QModelIndex(), rootItem->childCount(), rootItem->childCount());
        GraphTreeItem *item = new GraphTreeItem(object, predicate, rootItem);
        itemMap.insert(item->nodeId(), item); // Store the mapping
        rootItem->appendChild(item);
        endInsertRows();
    }

    void onChildrenLoaded(QString parentId, QVectorOfQStringPairs children) {
        QList<GraphTreeItem *> parents;

        if (!itemMap.contains(parentId))
          addTopLevelItem(parentId, "");

        parents.append(itemMap.values(parentId));

        // all the items relatives to the same node in the graph, can be more than one
        for(const auto &item: parents) {
          if (item->areChildrenLoaded()) {
            continue;
          }

          QModelIndex parentIndex = indexForItem(item);
          beginInsertRows(parentIndex, item->childCount(), item->childCount() + children.size() - 1);

          for (const auto &child: children) {
            GraphTreeItem *childItem = new GraphTreeItem(child.second, child.first, item);
            itemMap.insert(childItem->nodeId(), childItem);// Store the mapping
            item->appendChild(childItem);
          }

          item->setChildrenLoaded(true);

          endInsertRows();
        }
    }

    QString getPredicate(const QModelIndex &index) const {
        if (!index.isValid()) {
            return QString();
        }

        GraphTreeItem *item = static_cast<GraphTreeItem *>(index.internalPointer());
        return item->data(0, false).toString();
    }

    QString getObject(const QModelIndex &index) const {
        if (!index.isValid()) {
            return QString();
        }

        GraphTreeItem *item = static_cast<GraphTreeItem *>(index.internalPointer());
        return item->data(1, false).toString();
    }

public slots:
    void onRowExpanded(const QModelIndex &index) {
        if (!index.isValid()) {
            return;
        }

        GraphTreeItem *item = static_cast<GraphTreeItem *>(index.internalPointer());

        if (item->data(0) == "Constitutes")
          controllerWrapper->selectAllSubjects(item->data(0, false).toString().toStdString(),
                                               item->data(1, false).toString().toStdString());
    }

private:
    GraphTreeItem *rootItem;
    ControllerWrapper *controllerWrapper;
    QMultiHash<QString, GraphTreeItem*> itemMap; // Maps nodeId to GraphTreeItem
};

#endif//THREEDONT_GRAPH_TREE_MODEL_H
