# 🧠 BERTopic Tweet Explorer

An interactive web app built with Dash and Plotly to explore Twitter topic modeling results using [BERTopic](https://maartengr.github.io/BERTopic/). Designed by **Chris Reddish**, this tool visualizes topic proportions over time and lets users click to view the actual tweets for any topic-date combination.

---

## 🚀 Features

- 📊 Interactive stacked bar chart of topic proportions by date  
- 🖱️ Click a bar to reveal the associated tweets  
- 📁 Supports multiple model types (`UHC`, `LM`, `BT`) and topic numbers (`k`)  
- 🔍 Custom stopword filtering, including names and domain-specific noise

---

## 📁 File Structure

```
project/
├── app.py                          # Dash app with Plotly visualization
├── data/                           # Folder for CSV data
│   ├── *_document_info.csv         # File with original_text, topic, and date
│   └── *_topic_representation.csv  # File with topic number and top keywords
├── LICENSE                         # MIT License (recommended)
└── README.md                       # This file
```

---

## 📦 Requirements

Install required libraries with:

```bash
pip install -r requirements.txt
```

Minimum packages:
- `dash`
- `plotly`
- `pandas`

Optional (if you plan to run BERTopic in preprocessing):
- `bertopic`
- `nltk`
- `scikit-learn`
- `umap-learn`
- `hdbscan`
- `sentence-transformers`

---

## 📈 How to Run

1. Make sure your `data/` folder contains the proper CSV files.
2. Start the Dash app:

```bash
python app.py
```

3. Open in your browser:  
   [http://localhost:10000](http://localhost:10000)

---

## 🧠 Data Format

The app expects file pairs for each `stance` (`positive` or `negative`), model (`UHC`, `LM`, `BT`), and k-value (`k=5`, `k=10`, etc).

**File naming example:**
```
positive_UHC_k=10mini_document_info.csv
positive_UHC_k=10mini_topic_representation.csv
```

Each document file must include at least:
- `original_text`
- `Date`
- `Topic`

---

## 🛡️ License

MIT License © 2025 [Chris Reddish](https://www.linkedin.com/in/christopher-reddish-192a402a5)

---

## 📬 Contact

Got feedback or want to collaborate?  
Connect with me on [LinkedIn](https://www.linkedin.com/in/christopher-reddish-192a402a5)
