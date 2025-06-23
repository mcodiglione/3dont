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
  PropertiesMappingDialog(const QStringList& words,
                      const QStringList & options,
                      const QStringList & defaults = {},
                      QWidget* parent = nullptr)
      : QDialog(parent)  {

    setWindowTitle("Manual Mapping");
    QVBoxLayout* mainLayout = new QVBoxLayout(this);

    // Headers
    QHBoxLayout* headerLayout = new QHBoxLayout(this);
    headerLayout->addWidget(new QLabel("<b>Words</b>"));
    headerLayout->addWidget(new QLabel("<b>Mapped To</b>"));
    mainLayout->addLayout(headerLayout);

    QFormLayout* formLayout = new QFormLayout(this);

    // Create form rows
    for (int i = 0; i < words.size(); ++i) {
      auto* wordLabel = new QLabel(words[i], this);
      auto* comboBox = new QComboBox(this);
      comboBox->addItems(options);
      if (defaults.size() > i)
        comboBox->setCurrentText(defaults[i]);
      else
        comboBox->setCurrentIndex(0);  // Default to first option if no defaults provided

      formLayout->addRow(wordLabel, comboBox);
      comboBoxes.append(comboBox);
    }

    mainLayout->addLayout(formLayout);

    // OK and Cancel buttons
    QDialogButtonBox* buttonBox = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, this);
    mainLayout->addWidget(buttonBox);

    connect(buttonBox, &QDialogButtonBox::accepted, this, &PropertiesMappingDialog::onOkClicked);
    connect(buttonBox, &QDialogButtonBox::rejected, this, &PropertiesMappingDialog::reject);
  }

  // use only if the dialog was accepted
  QStringList getMappingResult() const {
    return result;
  }

  static QStringList getPropertiesMapping(QWidget* parent,
                                     const QStringList& options,
                                     const QStringList& words,
                                     const QStringList& defaults = {}) {
    PropertiesMappingDialog dialog(words, options, defaults, parent);
    if (dialog.exec() == QDialog::Accepted)
      return dialog.getMappingResult();

    return {};  // Return empty list if dialog was rejected
  }

private slots:
  void onOkClicked() {
    result.clear();
    for (QComboBox* comboBox : comboBoxes)
      result.append(comboBox->currentText());

    accept();  // Close dialog
  }

private:
  QList<QComboBox*> comboBoxes;
  QStringList result;
};

#endif // THREEDONT_PROPERTIES_MAPPING_SELECTION_H
