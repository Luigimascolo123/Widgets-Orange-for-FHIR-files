# 🍊 Widgets Orange per l'analisi di file FHIR

[![License](https://img.shields.io/badge/Licenza-MIT-blue.svg)](https://opensource.org/licenses/MIT) [![Python](https://img.shields.io/badge/Python-3.6%2B-green.svg)](https://www.python.org/) 

Questo repository contiene widget personalizzati per **Orange** che permettono di analizzare file conformi allo standard FHIR (Fast Healthcare Interoperability Resources). Ideali per esplorare dati sanitari in modo visivo e intuitivo!

---

## 📌 Introduzione

### Cos'è FHIR?
FHIR è uno standard sviluppato da HL7 per lo scambio elettronico di informazioni sanitarie. Organizza i dati in "risorse" (Resources), elementi modulari che rappresentano entità cliniche (pazienti, diagnosi, farmaci, ecc.).  
🔗 **Maggiori dettagli**: [Documentazione Ufficiale FHIR](https://www.hl7.org/fhir/overview.html)

### Cos'è Orange?
Orange è una piattaforma di **visual programming** per l'analisi dati, il machine learning e il data mining. Grazie ai widget, utenti possono costruire workflow interattivi senza scrivere codice.  
🖥️ **Scarica Orange**: [Sito Ufficiale](https://orange.biolab.si/)

---

## 🚀 Funzionalità

- **Widget personalizzati** per l'analisi di risorse FHIR specifiche.
- Integrazione diretta con Orange per una visualizzazione intuitiva dei dati.
- **3 workflow preconfigurati** per casi d'uso comuni.
- Estensibile ad altre risorse FHIR grazie a un'architettura modulare.

---

## ⚙️ Installazione

1. **Prerequisiti**:
   - Python 3.6 o superiore.
   - Orange Data Mining: installabile via `pip install orange3`.

2. **Clona il repository**:
   ```bash
   git clone https://github.com/tuo-repo/widgets-orange-fhir.git
   cd widgets-orange-fhir
   
3. **Installa i widget**:
   - Esegui gli script Python forniti per registrare i widget in Orange.
     (Dettagli completi nel file ISTRUZIONI.txt)

---

## 🎮 Utilizzo 

1. Avvia Orange dalla tua CLI con:
'''bash
orange-canvas

2. Nel menu Widget, cerca i nuovi widget FHIR (es: FHIR Patient Analyzer).

3. Trascina i widget sul canvas e connettili per creare il tuo workflow!

4. Carica i file FHIR (JSON/XML) e esplora i dati con grafici interattivi.

---

## 📂 Workflows Pronti
Il repository include 3 workflow dimostrativi:

- Analisi demografica pazienti (età, genere, regione).

- Visualizzazione terapie farmacologiche.

- Monitoraggio parametri clinici nel tempo.

**Apri i workflow con Orange dopo aver installato i widget!**

---

## 🔗 Risorse Utili
- Documentazione Orange : https://orangedatamining.com/docs/

- Documentazione FHIR: https://hl7.org/fhir/
