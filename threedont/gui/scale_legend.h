#ifndef THREEDONT_SCALE_LEGEND_H
#define THREEDONT_SCALE_LEGEND_H

#include <QPainter>
#include <QWidget>
#include <utility>

#define SCALE_MAX_HEIGHT 30

class ColorScaleLegend : public QWidget {
  Q_OBJECT
public:
  ColorScaleLegend(QList<QColor> colors, QStringList labels, QWidget *parent = nullptr) : QWidget(parent) {
    this->colors = std::move(colors);
    this->labels = std::move(labels);

    setMinimumHeight(fontMetrics().height() * 2);
  }

protected:
  void paintEvent(QPaintEvent *event) override {
    Q_UNUSED(event);
    QPainter painter(this);
    int width = this->width();
    int height = this->height();
    int textHeight = painter.fontMetrics().height();

    int colorStartX = painter.fontMetrics().horizontalAdvance(labels[0]);
    int colorEndX = width - painter.fontMetrics().horizontalAdvance(labels[labels.size() - 1]);
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

private:
  QList<QColor> colors;
  QStringList labels;
};
#endif//THREEDONT_SCALE_LEGEND_H
