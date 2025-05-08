#ifndef THREEDONT_GRAPH_TREE_ITEM_H
#define THREEDONT_GRAPH_TREE_ITEM_H

#include <QList>
#include <QString>
#include <QVariant>

class GraphTreeItem {
public:
  GraphTreeItem(QString object, QString predicate, GraphTreeItem *parent = nullptr);
  ~GraphTreeItem();

  void appendChild(GraphTreeItem *child);
  void removeChild(int row);
  GraphTreeItem *child(int row);

  [[nodiscard]] int childCount() const;
  [[nodiscard]] int columnCount() const;
  [[nodiscard]] QVariant data(int column, bool removeNS = true) const;

  GraphTreeItem *parent();
  [[nodiscard]] int childIndex() const;
  [[nodiscard]] bool areChildrenLoaded() const;
  void setChildrenLoaded(bool loaded);
  [[nodiscard]] QString nodeId() const;
  [[nodiscard]] bool isLeaf() const;

private:
  static QString removeNamespace(const QString &str);

  QString predicate;
  QString object;
  GraphTreeItem *parentItem;
  QList<GraphTreeItem *> childItems;
  bool childrenLoaded = false;
};

#endif // THREEDONT_GRAPH_TREE_ITEM_H
