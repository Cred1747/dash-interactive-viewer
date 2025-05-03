import os
import pandas as pd
import ast
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# === Local paths ===
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKING_DIR, "data")

# === Validate folder exists ===
if not os.path.exists(DATA_DIR):
    raise FileNotFoundError("❌ Folder not found: /data/Bert_4.1Mini_Extracted")

# === Index files ===
doc_files, label_files = [], []
for root, _, files in os.walk(DATA_DIR):
    for f in files:
        full = os.path.join(root, f)
        if "document_info" in f:
            doc_files.append(full)
        elif "topic_representation" in f:
            label_files.append(full)

index = {}
for doc in doc_files:
    base = os.path.basename(doc)
    polarity = "positive" if "positive" in base else "negative" if "negative" in base else None
    model = "UHC" if "UHC" in base else "LM" if "LM" in base else "BT" if "Brian" in base else None
    k_match = base.split("k=")[-1].replace("mini.csv", "").replace(".csv", "") if "k=" in base else None
    if polarity and model and k_match:
        model_id = f"{polarity}{model}"
        label = next((l for l in label_files if polarity in l and model in l and f"k={k_match}" in l), None)
        if label:
            index[(model_id, k_match)] = {"doc": doc, "label": label}

models = sorted(set(k[0] for k in index))
kvals = sorted(set(k[1] for k in index), key=int)

# === Dash app ===
app = Dash(__name__)
app.layout = html.Div([
    html.H2("Interactive Topic Proportions"),
    html.Div([
        html.Label("Model:"),
        dcc.Dropdown(id='model', options=[{"label": m, "value": m} for m in models], value=models[0] if models else None),
        html.Label("k-value:"),
        dcc.Dropdown(id='kval', options=[{"label": k, "value": k} for k in kvals], value=kvals[0] if kvals else None)
    ]),
    dcc.Graph(id='topic-graph')
])

@app.callback(
    Output('topic-graph', 'figure'),
    Input('model', 'value'),
    Input('kval', 'value')
)
def update_graph(model, kval):
    pair = (model, kval)
    if pair not in index:
        return px.bar(title="No data found.")

    df = pd.read_csv(index[pair]["doc"])
    labels_df = pd.read_csv(index[pair]["label"])

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.date
    df.dropna(subset=['Date', 'Topic'], inplace=True)

    grouped = df.groupby(['Date', 'Topic']).size().reset_index(name='Count')
    totals = grouped.groupby('Date')['Count'].sum().reset_index(name='Total')
    grouped = pd.merge(grouped, totals, on='Date')
    grouped['Proportion'] = grouped['Count'] / grouped['Total']

    labels_df['Label'] = labels_df['Representation'].apply(
        lambda x: " ".join(ast.literal_eval(x)[:5]) if pd.notnull(x) else "Unknown"
    )
    label_map = dict(zip(labels_df['Topic'], labels_df['Label']))
    grouped['Topic_Label'] = grouped['Topic'].map(label_map)
    grouped['DateTime'] = pd.to_datetime(grouped['Date'])

    fig = px.bar(
        grouped,
        x='DateTime',
        y='Proportion',
        color='Topic_Label',
        title=f"{model}, k={kval}",
        labels={'Proportion': 'Topic Proportion'},
        barmode='stack',
        template='plotly_white'
    )
    return fig

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run_server(host="0.0.0.0", port=port)


