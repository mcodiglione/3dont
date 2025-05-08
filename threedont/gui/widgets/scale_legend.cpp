#include "scale_legend.h"
#include <QPaintEvent>
#include <QPainter>
#include <QPalette>
#include <algorithm>

ColorScaleLegend::ColorScaleLegend(QList<QColor> colors, QStringList labels, QWidget *parent)
    : QWidget(parent), colors(std::move(colors)), labels(std::move(labels)) {
  setMinimumHeight(fontMetrics().height() * 2);
}

void ColorScaleLegend::paintEvent(QPaintEvent *event) {
  Q_UNUSED(event);
  QPainter painter(this);
  int width = this->width();
  int height = this->height();
  int textHeight = painter.fontMetrics().height();

  int colorStartX = painter.fontMetrics().horizontalAdvance(labels[0]);
  int colorEndX = width - painter.fontMetrics().horizontalAdvance(labels.last());
  int colorWidth = colorEndX - colorStartX;

  int scaleHeight = std::min(height - textHeight, SCALE_MAX_HEIGHT);
  QLinearGradient gradient(0, 0, colorWidth, 0);
  for (int i = 0; i < colors.size(); ++i)
    gradient.setColorAt(static_cast<qreal>(i) / (colors.size() - 1), colors[i]);

  painter.fillRect(colorStartX, 0, colorWidth, scaleHeight, gradient);

  painter.setPen(palette().color(QPalette::Text));
  for (int i = 0; i < labels.size(); ++i) {
    int x = static_cast<qreal>(i) / (labels.size() - 1) * colorWidth + colorStartX;
    int textWidth = painter.fontMetrics().horizontalAdvance(labels[i]);
    painter.drawText(x - textWidth / 2, scaleHeight + textHeight, labels[i]);
    painter.drawLine(x, 0, x, scaleHeight);
  }
}
