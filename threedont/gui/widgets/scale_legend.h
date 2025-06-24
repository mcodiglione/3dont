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
  void mousePressEvent(QMouseEvent* aEvent) override;
  void mouseMoveEvent(QMouseEvent* aEvent) override;
  void mouseReleaseEvent(QMouseEvent* aEvent) override;
  void resizeEvent(QResizeEvent *event) override;

signals:
  void rangeUpdated(double min, double max);

private:
  QList<QColor> colors;
  QStringList labels;
  double absMin, absMax, currMin, currMax;
  int colorStartX, colorEndX, scaleHeight;

  QRect legendRegion;

  int barX[2] = {-1, -1};
  int currentSlider = -1;

  int getXInLegendRegion(int x);
  double maxXtoValueInRegion(int x);
  void updateLegendFromSliders();
  void drawSliderHandle(QPainter *painter, int x, int height);
};

#endif // THREEDONT_SCALE_LEGEND_H