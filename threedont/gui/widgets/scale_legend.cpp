#include "scale_legend.h"
#include <QPaintEvent>
#include <QPainter>
#include <QPalette>
#include <QStyleOptionSlider>
#include <algorithm>
#include <iostream>

#define HANDLE_WIDTH 8
#define HANDLE_HEIGHT_RATIO 1.0

qreal remap(qreal value, qreal inMin, qreal inMax, qreal outMin, qreal outMax) {
  return outMin + (value - inMin) * (outMax - outMin) / (inMax - inMin);
}

ColorScaleLegend::ColorScaleLegend(QList<QColor> colors, QStringList labels, QWidget *parent)
    : QWidget(parent), colors(std::move(colors)), labels(std::move(labels)) {
  setMinimumHeight(fontMetrics().height() * 2);

  absMin = this->labels[0].toDouble();
  absMax = this->labels.last().toDouble();
  currMin = absMin;
  currMax = absMax;
}

void ColorScaleLegend::resizeEvent(QResizeEvent *event) {
  QWidget::resizeEvent(event); // Call base implementation
  const QFontMetrics fm = fontMetrics();

  int oldColorStartX = colorStartX;
  int oldColorEndX = colorEndX;

  colorStartX = fm.horizontalAdvance(labels[0]); // optionally divide by 2
  colorEndX = this->width() - fm.horizontalAdvance(labels.last()); // optionally divide by 2
  scaleHeight = std::min(this->height() - fm.height(), SCALE_MAX_HEIGHT);

  int colorWidth = colorEndX - colorStartX;
  legendRegion = QRect(colorStartX, 0, colorWidth, scaleHeight);

  if (barX[0] == -1) { // Initialize positions when size is set
    barX[0] = colorStartX;
    barX[1] = colorEndX;
  } else {
    barX[0] = remap(barX[0], oldColorStartX, oldColorEndX, colorStartX, colorEndX);
    barX[1] = remap(barX[1], oldColorStartX, oldColorEndX, colorStartX, colorEndX);
  }

  update(); // Schedule repaint in case layout has changed
}

void ColorScaleLegend::paintEvent(QPaintEvent *event) {
  Q_UNUSED(event);
  if (barX[0] == -1) { // initialize positions when size is set (maybe can be done in constructor)
    barX[0] = colorStartX;
    barX[1] = colorEndX;
  }

  int colorWidth = colorEndX - colorStartX;
  QLinearGradient gradient(colorStartX, 0, colorStartX + colorWidth, 0);
  gradient.setColorAt(0.0, colors.first());
  for (int i = 0; i < colors.size(); ++i)
    gradient.setColorAt(remap(remap(i, 0, colors.size() - 1, currMin, currMax), absMin, absMax, 0, 1), colors[i]);

  QPainter painter(this);
  painter.fillRect(colorStartX, 0, colorWidth, scaleHeight, gradient);

  painter.setPen(palette().color(QPalette::Text));
  for (int i = 0; i < labels.size(); ++i) {
    int x = static_cast<qreal>(i) / (labels.size() - 1) * colorWidth + colorStartX;
    int textWidth = painter.fontMetrics().horizontalAdvance(labels[i]);
    painter.drawText(x - textWidth / 2, scaleHeight + painter.fontMetrics().height(), labels[i]);
    painter.drawLine(x, 0, x, scaleHeight);
  }

  drawSliderHandle(&painter, barX[0], scaleHeight);
  drawSliderHandle(&painter, barX[1], scaleHeight);
}

int ColorScaleLegend::getXInLegendRegion(int x) {
  return std::max(legendRegion.left(), std::min(x, legendRegion.right()));
}

double ColorScaleLegend::maxXtoValueInRegion(int x) {
  double factor = static_cast<double>(x - legendRegion.left()) / legendRegion.width();
  return absMin + factor * (absMax - absMin);
}

void ColorScaleLegend::updateLegendFromSliders() {
  currMin = maxXtoValueInRegion(barX[0]);
  currMax = maxXtoValueInRegion(barX[1]);
  update();
}

void ColorScaleLegend::mousePressEvent(QMouseEvent *aEvent) {
  if (aEvent->buttons() & Qt::LeftButton && legendRegion.contains(aEvent->pos())) {
    if (abs(aEvent->pos().x() - barX[0]) < abs(aEvent->pos().x() - barX[1]))
      currentSlider = 0;
    else
      currentSlider = 1;
    barX[currentSlider] = getXInLegendRegion(aEvent->pos().x());
    updateLegendFromSliders();
  } else
    QWidget::mousePressEvent(aEvent);
}

void ColorScaleLegend::mouseMoveEvent(QMouseEvent *aEvent) {
  if (aEvent->buttons() & Qt::LeftButton && currentSlider != -1) {
    barX[currentSlider] = getXInLegendRegion(aEvent->pos().x());
    if (barX[0] >= barX[1])
      barX[currentSlider] = barX[1-currentSlider] + (currentSlider == 0 ? -1 : 1); // Prevent overlap

    updateLegendFromSliders();
  } else
    QWidget::mouseMoveEvent(aEvent);
}

void ColorScaleLegend::mouseReleaseEvent(QMouseEvent *aEvent) {
  if (aEvent->button() == Qt::LeftButton) {
    currentSlider = -1; // Reset the slider when the mouse is released
    emit rangeUpdated(currMin, currMax);
    std::cout << "Range updated: " << currMin << " - " << currMax << std::endl;
  } else
    QWidget::mouseReleaseEvent(aEvent);
}

void ColorScaleLegend::drawSliderHandle(QPainter *painter, int x, int height) {
  int handleHeight = height * HANDLE_HEIGHT_RATIO;
  QRect handleRect(x - HANDLE_WIDTH/2, height / 2 - handleHeight/2, HANDLE_WIDTH, handleHeight);
  painter->save();
  painter->setRenderHint(QPainter::Antialiasing);
  painter->setBrush(palette().color(QPalette::Button));
  painter->setPen(palette().color(QPalette::Dark));
  painter->drawRoundedRect(handleRect, 2, 2);
  painter->restore();
}
