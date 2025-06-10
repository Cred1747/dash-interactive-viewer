import os
import re
import pandas as pd
import ast
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

# === Local paths ===
WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(WORKING_DIR, "data")

# === Validate folder exists ===
if not os.path.exists(DATA_DIR):
    raise FileNotFoundError(f"❌ Folder not found: {DATA_DIR}")

# === Index files ===
doc_files, label_files = [], []
for root, _, files in os.walk(DATA_DIR):
    for f in files:
        if not f.endswith(".csv"):
            continue
        full = os.path.join(root, f)
        if "document_info" in f:
            doc_files.append(full)
        elif "topic_representation" in f:
            label_files.append(full)

index = {}
for doc in doc_files:
    base = os.path.basename(doc)

    # Extract polarity
    polarity = None
    if "positive" in base:
        polarity = "positive"
    elif "negative" in base:
        polarity = "negative"

    # Extract model
    model = None
    if "UHC" in base:
        model = "UHC"
    elif "LM" in base:
        model = "LM"
    elif "BTV3" in base:
        model = "BTV3"
    elif "BT" in base:
        model = "BT"

    # Extract k-value using regex
    k_search = re.search(r'k=(\d+)', base)
    k_match = k_search.group(1) if k_search else None

    print(f"Parsing: {base} → polarity={polarity}, model={model}, k={k_match}")

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
    html.Div([
        html.H4("Prime k values"),
        html.Ul([
            html.Li("BTV3 (Brian Thompson): Positive k = 8, Negative k = 6"),
            html.Li("LM (Luigi Mangione): Positive k = 8, Negative k = 8"),
            html.Li("UHC (United Health Care): Positive k = 8, Negative k = 7")
        ])
    ], style={"marginBottom": "20px", "marginTop": "10px"}),

    dcc.Graph(id='topic-graph'),
    html.H4("Tweets for Selected Topic & Date"),
    html.Div(id='tweet-output', style={"whiteSpace": "pre-wrap", "maxHeight": "400px", "overflowY": "scroll", "border": "1px solid #ccc", "padding": "10px"})
])

from dash.dependencies import Input, Output
import itertools

@app.callback(
    Output('topic-graph', 'figure'),
    Output('tweet-output', 'children'),
    Input('model', 'value'),
    Input('kval', 'value'),
    Input('topic-graph', 'clickData')
)
def update_graph(model, kval, clickData):
    pair = (model, kval)
    if pair not in index:
        return px.bar(title="No data found."), "No tweets to display."

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

    unique_labels = grouped['Topic_Label'].unique()
    import plotly.colors
    color_sequence = plotly.colors.qualitative.Alphabet
    extended_colors = (
        list(itertools.islice(itertools.cycle(color_sequence), len(unique_labels)))
        if len(unique_labels) > len(color_sequence) else color_sequence[:len(unique_labels)]
    )

    fig = px.bar(
        grouped,
        x='DateTime',
        y='Proportion',
        color='Topic_Label',
        title=f"{model}, k={kval}",
        labels={'Proportion': 'Topic Proportion'},
        barmode='stack',
        template='plotly_white',
        color_discrete_sequence=extended_colors
    )
    

    # === Extract clicked info and show tweets ===
    if clickData:
        clicked_date = pd.to_datetime(clickData['points'][0]['x']).date()
        clicked_label = clickData['points'][0]['curveNumber']
        label_name = grouped['Topic_Label'].unique()[clicked_label]
        matched_topic = grouped[
            (grouped['Date'] == clicked_date) & (grouped['Topic_Label'] == label_name)
        ]['Topic'].values

        if matched_topic.size > 0:
            topic = matched_topic[0]
            tweet_col = 'original_text' if 'original_text' in df.columns else 'Document'
            tweets = df[
                (df['Date'] == clicked_date) & (df['Topic'] == topic)
            ][tweet_col].dropna().tolist()
            if tweets:
                return fig, f"📅 {clicked_date} — Topic {topic} — {label_name}\n\n" + "\n\n".join(tweets)
            else:
                return fig, f"No tweets found for {label_name} on {clicked_date}."
        else:
            return fig, "No matching topic found for selected bar."

    return fig, "Click a bar to see tweets for that topic and date."


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

