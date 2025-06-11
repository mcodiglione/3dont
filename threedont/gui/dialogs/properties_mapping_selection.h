#ifndef THREEDONT_PROPERTIES_MAPPING_SELECTION_H
#define THREEDONT_PROPERTIES_MAPPING_SELECTION_H

#include <QDialog>
#include <QMap>
#include <QStringList>
#include <QComboBox>
#include <QVBoxLayout>
#include <QFormLayout>
#include <QLabel>
#include <QPushButton>
#include <QDialogButtonBox>

class PropertiesMappingDialog : public QDialog {
  Q_OBJECT

public:
  PropertiesMappingDialog(const QStringList& unmappedList,
                      const QList<QStringList>& parsedOntologySchema,
                      const QMap<QString, QString>& typeDict,
                      QWidget* parent = nullptr)
      : QDialog(parent), typeDict(typeDict), parsedOntologySchema(parsedOntologySchema) {

    setWindowTitle("Manual Mapping");
    QVBoxLayout* mainLayout = new QVBoxLayout(this);

    // Headers
    QHBoxLayout* headerLayout = new QHBoxLayout(this);
    headerLayout->addWidget(new QLabel("<b>Words</b>"));
    headerLayout->addWidget(new QLabel("<b>Mapped To</b>"));
    mainLayout->addLayout(headerLayout);

    QFormLayout* formLayout = new QFormLayout(this);

    // Flatten the ontology schema
    QStringList flattenedSchema;
    for (const QStringList& sublist : parsedOntologySchema)
      flattenedSchema.append(sublist);

    // Create form rows
    for (const QString& word : unmappedList) {
      QLabel* wordLabel = new QLabel(word);
      QComboBox* comboBox = new QComboBox();
      comboBox->addItems(flattenedSchema);
      formLayout->addRow(wordLabel, comboBox);
      comboBoxes[word] = comboBox;
    }

    mainLayout->addLayout(formLayout);

    // OK and Cancel buttons
    QDialogButtonBox* buttonBox = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, this);
    mainLayout->addWidget(buttonBox);

    connect(buttonBox, &QDialogButtonBox::accepted, this, &PropertiesMappingDialog::onOkClicked);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &PropertiesMappingDialog::reject);
  }

  // use only if the dialog was accepted
  QMap<QString, QStringList> getMappingResult() const {
    return mappingResult;
  }

private slots:
  void onOkClicked() {
    mappingResult.clear();
    for (const auto& [word, comboBox] : comboBoxes.toStdMap()) {
      QString mapped = comboBox->currentText();

      if (!mapped.isEmpty()) {
        for (int i = 0; i < parsedOntologySchema.size(); ++i) {
          if (parsedOntologySchema[i].contains(mapped)) {
            QString type = typeDict.value(QString::number(i));
            mappingResult[word] = {mapped, type};
            break;
          }
        }
      }
    }
    accept();  // Close dialog
  }

private:
  QMap<QString, QComboBox*> comboBoxes;
  QMap<QString, QStringList> mappingResult;
  QMap<QString, QString> typeDict;
  QList<QStringList> parsedOntologySchema;
};

#endif // THREEDONT_PROPERTIES_MAPPING_SELECTION_H
