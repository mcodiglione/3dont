#ifndef THREEDONT_TYPES_H
#define THREEDONT_TYPES_H

#include <QMetaObject>
#include <QMetaType>
#include <QVector>
#include <QPair>
#include <QString>


using QVectorOfQStringPairs = QVector<QPair<QString, QString>>;


inline void declareAllMetaTypes() {
    qRegisterMetaType<QVectorOfQStringPairs>("QVectorOfQStringPairs");

}

#endif//THREEDONT_TYPES_H
