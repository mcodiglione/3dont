#ifndef THREEDONT_SCALE_LEGEND_H
#define THREEDONT_SCALE_LEGEND_H

#include <QColor>
#include <QList>
#include <QStringList>
#include <QWidget>

#define SCALE_MAX_HEIGHT 30

class ColorScaleLegend : public QWidget {
  Q_OBJECT
public:
  ColorScaleLegend(QList<QColor> colors, QStringList labels, QWidget *parent = nullptr);

protected:
  void paintEvent(QPaintEvent *event) override;

private:
  QList<QColor> colors;
  QStringList labels;
};

#endif // THREEDONT_SCALE_LEGEND_H