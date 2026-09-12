from __future__ import annotations

from io import BytesIO
from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image, ImageDraw, ImageFont


st.set_page_config(
    page_title="Store Purchase Cluster Simulation",
    page_icon="cart",
    layout="wide",
)


def inject_galaxy_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --panel: rgba(12, 18, 36, 0.82);
            --panel-border: rgba(149, 180, 255, 0.24);
            --text: #edf2ff;
            --muted: #b6c2df;
            --accent: #9ec5fe;
        }

        .stApp {
            color: var(--text);
            background:
                radial-gradient(circle at 18% 22%, rgba(68, 92, 180, 0.38) 0 2px, transparent 3px),
                radial-gradient(circle at 72% 18%, rgba(255, 255, 255, 0.7) 0 1px, transparent 2px),
                radial-gradient(circle at 84% 68%, rgba(158, 197, 254, 0.5) 0 1px, transparent 2px),
                radial-gradient(circle at 32% 78%, rgba(255, 235, 186, 0.65) 0 1px, transparent 2px),
                linear-gradient(142deg, #060814 0%, #111b3c 42%, #211338 72%, #060814 100%);
            background-attachment: fixed;
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
                radial-gradient(circle, rgba(255, 255, 255, 0.56) 0 1px, transparent 1.6px),
                radial-gradient(circle, rgba(158, 197, 254, 0.42) 0 1px, transparent 1.8px);
            background-position: 0 0, 42px 24px;
            background-size: 96px 96px, 132px 132px;
            opacity: 0.45;
        }

        [data-testid="stSidebar"], [data-testid="stHeader"] {
            background: rgba(5, 8, 20, 0.72);
        }

        [data-testid="stMetric"], [data-testid="stDataFrame"], .stTabs [data-baseweb="tab-panel"] {
            background: var(--panel);
            border: 1px solid var(--panel-border);
            border-radius: 8px;
            padding: 0.75rem;
        }

        h1, h2, h3, p, label, span, div {
            letter-spacing: 0;
        }

        .stCaption, [data-testid="stMarkdownContainer"] p {
            color: var(--muted);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_galaxy_theme()


PRODUCTS = [
    {"sku": "APL-001", "name": "Organic Apples", "category": "Produce", "price": 4.99, "color": "#2f9e44"},
    {"sku": "BAN-002", "name": "Banana Bunch", "category": "Produce", "price": 2.49, "color": "#f1c40f"},
    {"sku": "MLK-003", "name": "Whole Milk", "category": "Dairy", "price": 3.79, "color": "#74c0fc"},
    {"sku": "YGT-004", "name": "Greek Yogurt", "category": "Dairy", "price": 5.49, "color": "#91a7ff"},
    {"sku": "BRD-005", "name": "Sourdough Bread", "category": "Bakery", "price": 6.25, "color": "#d9480f"},
    {"sku": "CKE-006", "name": "Chocolate Cake", "category": "Bakery", "price": 12.99, "color": "#7b341e"},
    {"sku": "CHP-007", "name": "Potato Chips", "category": "Snacks", "price": 3.99, "color": "#fab005"},
    {"sku": "SAL-008", "name": "Trail Mix", "category": "Snacks", "price": 7.29, "color": "#a16207"},
    {"sku": "SOD-009", "name": "Sparkling Soda", "category": "Drinks", "price": 4.59, "color": "#e03131"},
    {"sku": "COF-010", "name": "Cold Brew Coffee", "category": "Drinks", "price": 5.99, "color": "#343a40"},
    {"sku": "SOA-011", "name": "Hand Soap", "category": "Household", "price": 3.49, "color": "#20c997"},
    {"sku": "PPR-012", "name": "Paper Towels", "category": "Household", "price": 8.99, "color": "#adb5bd"},
    {"sku": "SHM-013", "name": "Shampoo", "category": "Personal Care", "price": 9.49, "color": "#845ef7"},
    {"sku": "VIT-014", "name": "Daily Vitamins", "category": "Personal Care", "price": 14.99, "color": "#ff922b"},
    {"sku": "DOG-015", "name": "Dog Treats", "category": "Pet", "price": 6.99, "color": "#795548"},
    {"sku": "CAT-016", "name": "Cat Litter", "category": "Pet", "price": 13.49, "color": "#868e96"},
]

CATEGORY_ORDER = sorted({product["category"] for product in PRODUCTS})
PERSONAS = {
    "Budget weekly shopper": {"basket": 7, "spend": 0.85, "discount": 0.22, "categories": ["Produce", "Dairy", "Bakery"]},
    "Convenience snacker": {"basket": 3, "spend": 1.05, "discount": 0.05, "categories": ["Snacks", "Drinks", "Bakery"]},
    "Home restocker": {"basket": 6, "spend": 1.2, "discount": 0.12, "categories": ["Household", "Personal Care", "Pet"]},
    "Premium mixed cart": {"basket": 8, "spend": 1.35, "discount": 0.08, "categories": ["Produce", "Personal Care", "Drinks", "Pet"]},
}


@st.cache_data
def product_image_bytes(name: str, category: str, color: str) -> bytes:
    image = Image.new("RGB", (360, 260), "#f4f6f8")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((18, 16, 342, 244), radius=18, fill="#ffffff", outline="#d6dee6", width=2)
    draw.rounded_rectangle((34, 32, 326, 174), radius=14, fill="#eef3f7")
    draw_product_icon(draw, name, category, color)

    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        sub_font = ImageFont.truetype("arial.ttf", 17)
    except OSError:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    wrapped_name = name if len(name) <= 18 else name[:17] + "."
    draw.text((55, 184), wrapped_name, fill="#212529", font=title_font)
    draw.text((55, 214), category, fill="#495057", font=sub_font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def draw_product_icon(draw: ImageDraw.ImageDraw, name: str, category: str, color: str) -> None:
    if "Apple" in name:
        for box in [(103, 76, 171, 145), (153, 76, 221, 145), (128, 108, 196, 176)]:
            draw.ellipse(box, fill="#e03131", outline="#9b1c1c", width=3)
        draw.line((160, 72, 169, 48), fill="#5c3d2e", width=5)
        draw.ellipse((170, 48, 214, 70), fill="#2f9e44")
    elif "Banana" in name:
        draw.arc((78, 56, 276, 182), start=20, end=168, fill="#f1c40f", width=26)
        draw.arc((86, 62, 284, 188), start=20, end=168, fill="#b7791f", width=4)
    elif "Milk" in name:
        draw.polygon([(130, 56), (210, 56), (230, 90), (230, 172), (110, 172), (110, 90)], fill="#ffffff", outline="#4dabf7")
        draw.rectangle((124, 98, 216, 136), fill="#74c0fc")
        draw.text((146, 108), "MILK", fill="#123", font=ImageFont.load_default())
    elif "Yogurt" in name:
        draw.rectangle((116, 86, 224, 166), fill="#f8f9fa", outline=color, width=4)
        draw.polygon([(106, 86), (234, 86), (218, 64), (122, 64)], fill=color)
        draw.ellipse((140, 110, 200, 150), fill="#d0ebff")
    elif "Bread" in name:
        draw.rounded_rectangle((90, 84, 252, 164), radius=34, fill="#f59f00", outline="#9c5c1a", width=4)
        for x in [124, 164, 204]:
            draw.arc((x - 16, 100, x + 26, 138), 200, 330, fill="#8a4b16", width=4)
    elif "Cake" in name:
        draw.rectangle((92, 104, 250, 166), fill="#7b341e")
        draw.rectangle((92, 82, 250, 108), fill="#f783ac")
        for x in [122, 172, 222]:
            draw.line((x, 82, x, 56), fill="#343a40", width=3)
            draw.ellipse((x - 5, 48, x + 5, 60), fill="#ffd43b")
    elif "Chips" in name:
        draw.polygon([(112, 56), (232, 72), (220, 174), (96, 162)], fill="#fab005", outline="#c47f00", width=4)
        draw.ellipse((138, 96, 194, 136), fill="#ffe066", outline="#c47f00", width=3)
    elif "Trail Mix" in name:
        draw.rounded_rectangle((92, 72, 252, 170), radius=16, fill="#fff3bf", outline="#a16207", width=4)
        for x, y, fill in [(126, 110, "#795548"), (160, 132, "#f08c00"), (198, 104, "#8ce99a"), (212, 142, "#a16207")]:
            draw.ellipse((x - 12, y - 10, x + 12, y + 10), fill=fill)
    elif "Soda" in name:
        draw.rectangle((132, 56, 212, 170), fill="#e03131", outline="#7f1d1d", width=4)
        draw.rectangle((146, 40, 198, 60), fill="#adb5bd", outline="#495057")
        draw.ellipse((146, 90, 198, 138), fill="#ffffff")
    elif "Coffee" in name:
        draw.rounded_rectangle((112, 62, 224, 172), radius=14, fill="#343a40", outline="#111827", width=4)
        draw.rectangle((132, 44, 204, 66), fill="#ced4da", outline="#495057")
        draw.rectangle((126, 104, 210, 136), fill="#f8f9fa")
    elif "Soap" in name:
        draw.rounded_rectangle((114, 74, 224, 170), radius=18, fill="#20c997", outline="#0b7285", width=4)
        draw.rectangle((148, 54, 190, 78), fill="#ced4da", outline="#495057")
        draw.arc((134, 106, 204, 142), 0, 180, fill="#ffffff", width=5)
    elif "Paper" in name:
        for offset in [0, 28]:
            draw.ellipse((104 + offset, 66, 184 + offset, 166), fill="#f8f9fa", outline="#868e96", width=4)
            draw.ellipse((128 + offset, 94, 160 + offset, 138), fill="#dee2e6")
    elif "Shampoo" in name:
        draw.rounded_rectangle((124, 60, 218, 174), radius=16, fill="#845ef7", outline="#4c1d95", width=4)
        draw.rectangle((146, 42, 196, 64), fill="#ced4da", outline="#495057")
        draw.rectangle((140, 102, 202, 132), fill="#ffffff")
    elif "Vitamins" in name:
        draw.rounded_rectangle((120, 66, 222, 174), radius=14, fill="#ff922b", outline="#b45309", width=4)
        draw.rectangle((138, 44, 204, 68), fill="#ced4da", outline="#495057")
        draw.rectangle((142, 104, 202, 136), fill="#ffffff")
        draw.text((158, 112), "VIT", fill="#212529", font=ImageFont.load_default())
    elif "Dog" in name:
        draw.ellipse((104, 80, 160, 136), fill="#795548")
        draw.ellipse((184, 80, 240, 136), fill="#795548")
        draw.rounded_rectangle((112, 104, 232, 168), radius=28, fill="#a16207", outline="#5c3d2e", width=4)
    elif "Cat" in name:
        draw.rectangle((102, 78, 244, 170), fill="#dee2e6", outline="#868e96", width=4)
        draw.polygon([(126, 78), (148, 48), (170, 78)], fill="#dee2e6", outline="#868e96")
        draw.polygon([(188, 78), (214, 48), (228, 78)], fill="#dee2e6", outline="#868e96")
    else:
        draw.ellipse((122, 54, 238, 170), fill=color)
        draw.rectangle((158, 102, 202, 202), fill=color)


@st.cache_data
def build_transactions(transaction_count: int, seed: int, timeline_months: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    product_df = pd.DataFrame(PRODUCTS)
    product_lookup = {product["sku"]: product for product in PRODUCTS}
    persona_names = list(PERSONAS.keys())
    persona_weights = np.array([0.34, 0.28, 0.23, 0.15])

    transaction_rows: List[Dict] = []
    item_rows: List[Dict] = []

    for index in range(transaction_count):
        persona_name = rng.choice(persona_names, p=persona_weights)
        persona = PERSONAS[persona_name]
        customer_id = f"C{rng.integers(1000, 1065)}"
        purchase_age_months = int(rng.integers(0, timeline_months + 1))
        item_count = max(1, int(rng.normal(persona["basket"], 2)))
        hour = int(np.clip(rng.normal(18 if "weekly" in persona_name else 13, 4), 7, 22))
        weekday = int(rng.integers(0, 7))
        discount_rate = float(np.clip(rng.normal(persona["discount"], 0.06), 0, 0.45))
        loyalty_member = bool(rng.random() < (0.82 if discount_rate > 0.12 else 0.48))

        candidate_products = product_df[product_df["category"].isin(persona["categories"])]
        basket_skus = rng.choice(candidate_products["sku"], size=item_count, replace=True)

        subtotal = 0.0
        category_totals = dict.fromkeys(CATEGORY_ORDER, 0.0)
        basket_names = []

        transaction_id = f"T{index + 1:05d}"
        for sku in basket_skus:
            product = product_lookup[str(sku)]
            quantity = int(rng.choice([1, 1, 1, 2, 3]))
            unit_price = round(product["price"] * rng.normal(persona["spend"], 0.08), 2)
            line_total = round(quantity * unit_price, 2)
            subtotal += line_total
            category_totals[product["category"]] += line_total
            basket_names.append(product["name"])
            item_rows.append(
                {
                    "transaction_id": transaction_id,
                    "customer_id": customer_id,
                    "purchase_age_months": purchase_age_months,
                    "sku": product["sku"],
                    "product_name": product["name"],
                    "category": product["category"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                    "image": product_image_bytes(product["name"], product["category"], product["color"]),
                }
            )

        total = round(subtotal * (1 - discount_rate), 2)
        transaction_rows.append(
            {
                "transaction_id": transaction_id,
                "customer_id": customer_id,
                "persona": persona_name,
                "purchase_age_months": purchase_age_months,
                "item_count": item_count,
                "subtotal": round(subtotal, 2),
                "discount_rate": round(discount_rate, 3),
                "total": total,
                "hour": hour,
                "weekday": weekday,
                "weekend": weekday >= 5,
                "loyalty_member": loyalty_member,
                "basket_preview": ", ".join(basket_names[:4]),
                **{f"{category}_spend": round(value, 2) for category, value in category_totals.items()},
            }
        )

    return pd.DataFrame(transaction_rows), pd.DataFrame(item_rows)


def age_transactions(transactions: pd.DataFrame, simulation_age_months: int) -> pd.DataFrame:
    aged = transactions.copy()
    elapsed_months = (simulation_age_months - aged["purchase_age_months"]).clip(lower=0)
    age_factor = elapsed_months / max(simulation_age_months, 1)
    inflation_multiplier = 1 + (elapsed_months * 0.0035)
    recency_weight = np.exp(-elapsed_months / 10)

    aged["elapsed_months"] = elapsed_months.astype(int)
    aged["recency_weight"] = recency_weight.round(3)
    aged["aged_subtotal"] = (aged["subtotal"] * inflation_multiplier).round(2)
    aged["aged_total"] = (aged["total"] * inflation_multiplier).round(2)
    aged["aging_score"] = (age_factor * 100).round(1)
    aged["churn_risk"] = np.clip(0.12 + age_factor * 0.58 - aged["loyalty_member"].astype(float) * 0.16, 0.03, 0.92).round(3)
    aged["lifecycle_stage"] = np.select(
        [
            elapsed_months <= 3,
            elapsed_months <= 9,
            elapsed_months <= 18,
        ],
        ["New signal", "Maturing signal", "Aged signal"],
        default="Dormant signal",
    )
    return aged


def cluster_transactions(transactions: pd.DataFrame, cluster_count: int) -> pd.DataFrame:
    feature_columns = [
        "item_count",
        "aged_subtotal",
        "discount_rate",
        "aged_total",
        "hour",
        "elapsed_months",
        "recency_weight",
        "churn_risk",
        "weekend",
        "loyalty_member",
        *[f"{category}_spend" for category in CATEGORY_ORDER],
    ]
    features = transactions[feature_columns].astype(float)
    scaled_features = standardize(features.to_numpy())
    level_1_labels = kmeans(scaled_features, min(3, len(transactions)), seed=7)
    clusters = kmeans(scaled_features, cluster_count, seed=42)
    projection = pca_3d(scaled_features)

    clustered = transactions.copy()
    clustered["level_1_group"] = name_level_1_groups(clustered, level_1_labels)
    clustered["cluster"] = clusters.astype(str)
    clustered["x"] = projection[:, 0]
    clustered["y"] = projection[:, 1]
    clustered["z"] = projection[:, 2]
    return clustered


def name_level_1_groups(transactions: pd.DataFrame, labels: np.ndarray) -> np.ndarray:
    labeled = transactions.copy()
    labeled["_level_1_label"] = labels
    spend_columns = [f"{category}_spend" for category in CATEGORY_ORDER]
    group_names = {}

    for label, group in labeled.groupby("_level_1_label"):
        dominant_category = group[spend_columns].mean().idxmax().replace("_spend", "")
        avg_total = group["total"].mean()
        avg_items = group["item_count"].mean()

        if dominant_category in {"Produce", "Dairy", "Bakery"} and avg_total < 55:
            group_names[label] = "Fresh value baskets"
        elif dominant_category in {"Snacks", "Drinks"} or avg_items <= 4:
            group_names[label] = "Quick trip baskets"
        elif dominant_category in {"Household", "Personal Care", "Pet"}:
            group_names[label] = "Home stock-up baskets"
        else:
            group_names[label] = "Premium mixed baskets"

    return pd.Series(labels).map(group_names).to_numpy()


def standardize(values: np.ndarray) -> np.ndarray:
    means = values.mean(axis=0)
    stds = values.std(axis=0)
    stds[stds == 0] = 1
    return (values - means) / stds


def kmeans(values: np.ndarray, cluster_count: int, seed: int, max_iterations: int = 80) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centroid_indexes = rng.choice(len(values), size=cluster_count, replace=False)
    centroids = values[centroid_indexes].copy()
    labels = np.zeros(len(values), dtype=int)

    for _ in range(max_iterations):
        distances = np.linalg.norm(values[:, None, :] - centroids[None, :, :], axis=2)
        next_labels = distances.argmin(axis=1)

        if np.array_equal(labels, next_labels):
            break

        labels = next_labels
        for cluster_index in range(cluster_count):
            members = values[labels == cluster_index]
            if len(members):
                centroids[cluster_index] = members.mean(axis=0)
            else:
                centroids[cluster_index] = values[rng.integers(0, len(values))]

    return labels


def pca_3d(values: np.ndarray) -> np.ndarray:
    centered = values - values.mean(axis=0)
    _, _, components = np.linalg.svd(centered, full_matrices=False)
    projection = centered @ components[:3].T
    if projection.shape[1] < 3:
        projection = np.column_stack([projection, np.zeros(len(values))])
    return projection


def cluster_summary(clustered: pd.DataFrame) -> pd.DataFrame:
    return (
        clustered.groupby(["level_1_group", "cluster"])
        .agg(
            transactions=("transaction_id", "count"),
            avg_total=("total", "mean"),
            avg_aged_total=("aged_total", "mean"),
            avg_items=("item_count", "mean"),
            avg_discount=("discount_rate", "mean"),
            avg_age_months=("elapsed_months", "mean"),
            avg_churn_risk=("churn_risk", "mean"),
            loyalty_rate=("loyalty_member", "mean"),
            peak_hour=("hour", lambda series: int(round(series.mean()))),
        )
        .round(
            {
                "avg_total": 2,
                "avg_aged_total": 2,
                "avg_items": 1,
                "avg_discount": 3,
                "avg_age_months": 1,
                "avg_churn_risk": 3,
                "loyalty_rate": 2,
            }
        )
        .reset_index()
        .sort_values(["level_1_group", "cluster"])
    )


with st.sidebar:
    st.header("Simulation")
    transaction_count = st.slider("Test transactions", 80, 800, 260, 20)
    cluster_count = st.slider("Clusters", 2, 8, 4)
    timeline_months = st.slider("History window months", 6, 36, 24, 3)
    simulation_age_months = st.slider("Simulation age month", 0, timeline_months, min(12, timeline_months))
    seed = st.number_input("Random seed", min_value=1, max_value=9999, value=127, step=1)
    st.divider()
    color_by = st.radio("Map color", ["Level 1 group", "Detailed cluster"], horizontal=False)
    show_chart_grid = st.toggle("Show chart grid", value=False)
    selected_personas = st.multiselect("Filter personas", list(PERSONAS), default=list(PERSONAS))

transactions, items = build_transactions(transaction_count, int(seed), timeline_months)
aged_transactions = age_transactions(transactions, simulation_age_months)
clustered = cluster_transactions(aged_transactions, cluster_count)
filtered = clustered[clustered["persona"].isin(selected_personas)].copy()

st.title("Asterism Store Purchase Cluster Simulation")
st.caption("Galaxy-themed purchase constellations with product-like images, first-level basket groups, detailed clusters, and aging over time.")

if filtered.empty:
    st.warning("Select at least one persona to show clustered purchase simulations.")
    st.stop()

metric_a, metric_b, metric_c, metric_d = st.columns(4)
metric_a.metric("Transactions", f"{len(filtered):,}")
metric_b.metric("Aged revenue", f"${filtered['aged_total'].sum():,.0f}")
metric_c.metric("Avg aged basket", f"${filtered['aged_total'].mean():.2f}")
metric_d.metric("Avg age", f"{filtered['elapsed_months'].mean():.1f} mo")

tab_map, tab_time, tab_groups, tab_clusters, tab_transactions, tab_catalog = st.tabs(
    ["3D galaxy map", "Aging timeline", "Level 1 groups", "Cluster explorer", "Transactions", "Product catalog"]
)

with tab_map:
    color_column = "level_1_group" if color_by == "Level 1 group" else "cluster"
    axis_style = (
        dict(
            showgrid=True,
            gridcolor="rgba(158,197,254,0.18)",
            zeroline=True,
            zerolinecolor="rgba(255,255,255,0.2)",
            showbackground=True,
            backgroundcolor="rgba(5, 8, 20, 0.28)",
        )
        if show_chart_grid
        else dict(showgrid=False, zeroline=False, showbackground=False)
    )
    fig = px.scatter_3d(
        filtered,
        x="x",
        y="y",
        z="z",
        color=color_column,
        size="total",
        hover_data=[
            "transaction_id",
            "customer_id",
            "level_1_group",
            "cluster",
            "persona",
            "total",
            "aged_total",
            "item_count",
            "discount_rate",
            "elapsed_months",
            "lifecycle_stage",
            "churn_risk",
        ],
        labels={
            "x": "Behavior component 1",
            "y": "Behavior component 2",
            "z": "Behavior component 3",
            "level_1_group": "Level 1 group",
            "cluster": "Cluster",
        },
        color_discrete_sequence=px.colors.qualitative.Set2,
        height=620,
    )
    fig.update_traces(marker=dict(opacity=0.78, line=dict(width=0.5, color="#ffffff")))
    fig.update_layout(
        margin=dict(l=0, r=0, t=24, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#edf2ff"),
        scene=dict(
            xaxis_title="Behavior 1",
            yaxis_title="Behavior 2",
            zaxis_title="Behavior 3",
            bgcolor="rgba(5, 8, 20, 0.64)",
            xaxis=axis_style,
            yaxis=axis_style,
            zaxis=axis_style,
            camera=dict(eye=dict(x=1.55, y=1.35, z=0.95)),
        ),
        legend_title_text="Group" if color_by == "Level 1 group" else "Cluster",
    )
    st.plotly_chart(fig, width="stretch")

with tab_time:
    timeline = []
    for month in range(timeline_months + 1):
        month_frame = age_transactions(transactions, month)
        timeline.append(
            {
                "month": month,
                "aged_revenue": month_frame["aged_total"].sum(),
                "avg_age_months": month_frame["elapsed_months"].mean(),
                "avg_churn_risk": month_frame["churn_risk"].mean(),
                "active_weight": month_frame["recency_weight"].sum(),
            }
        )
    timeline_df = pd.DataFrame(timeline)
    timeline_long = timeline_df.melt(
        id_vars="month",
        value_vars=["aged_revenue", "avg_age_months", "avg_churn_risk", "active_weight"],
        var_name="aging_metric",
        value_name="value",
    )
    time_fig = px.line(
        timeline_long,
        x="month",
        y="value",
        color="aging_metric",
        markers=True,
        labels={"month": "Simulation month", "value": "Metric value", "aging_metric": "Aging metric"},
        height=420,
        color_discrete_sequence=["#9ec5fe", "#ffd43b", "#ff8787", "#69db7c"],
    )
    time_fig.add_vline(x=simulation_age_months, line_width=3, line_dash="dot", line_color="#ffffff")
    time_fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(5, 8, 20, 0.58)",
        font=dict(color="#edf2ff"),
        legend_title_text="Metric",
        margin=dict(l=8, r=8, t=16, b=8),
    )
    time_fig.update_xaxes(
        showgrid=show_chart_grid,
        gridcolor="rgba(158,197,254,0.18)",
        zeroline=show_chart_grid,
        zerolinecolor="rgba(255,255,255,0.2)",
    )
    time_fig.update_yaxes(
        showgrid=show_chart_grid,
        gridcolor="rgba(158,197,254,0.18)",
        zeroline=show_chart_grid,
        zerolinecolor="rgba(255,255,255,0.2)",
    )
    st.plotly_chart(time_fig, width="stretch")

    stage_summary = (
        filtered.groupby("lifecycle_stage")
        .agg(
            transactions=("transaction_id", "count"),
            aged_revenue=("aged_total", "sum"),
            avg_age_months=("elapsed_months", "mean"),
            avg_churn_risk=("churn_risk", "mean"),
            active_weight=("recency_weight", "sum"),
        )
        .round({"aged_revenue": 2, "avg_age_months": 1, "avg_churn_risk": 3, "active_weight": 1})
        .reset_index()
        .sort_values("avg_age_months")
    )
    st.dataframe(stage_summary, width="stretch", hide_index=True)

with tab_groups:
    group_summary = (
        filtered.groupby("level_1_group")
        .agg(
            transactions=("transaction_id", "count"),
            aged_revenue=("aged_total", "sum"),
            avg_aged_total=("aged_total", "mean"),
            avg_items=("item_count", "mean"),
            avg_discount=("discount_rate", "mean"),
            avg_age_months=("elapsed_months", "mean"),
            avg_churn_risk=("churn_risk", "mean"),
            loyalty_rate=("loyalty_member", "mean"),
        )
        .round(
            {
                "aged_revenue": 2,
                "avg_aged_total": 2,
                "avg_items": 1,
                "avg_discount": 3,
                "avg_age_months": 1,
                "avg_churn_risk": 3,
                "loyalty_rate": 2,
            }
        )
        .reset_index()
        .sort_values("transactions", ascending=False)
    )
    st.dataframe(group_summary, width="stretch", hide_index=True)

    selected_group = st.selectbox("Inspect level 1 group", group_summary["level_1_group"])
    group_rows = filtered[filtered["level_1_group"] == selected_group]
    group_items = items[items["transaction_id"].isin(group_rows["transaction_id"])]
    group_products = (
        group_items.groupby(["product_name", "category", "image"], as_index=False)
        .agg(units=("quantity", "sum"), sales=("line_total", "sum"))
        .sort_values(["units", "sales"], ascending=False)
        .head(8)
    )
    st.subheader(f"{selected_group} product signals")
    group_columns = st.columns(4)
    for card_index, row in enumerate(group_products.itertuples(index=False)):
        with group_columns[card_index % 4]:
            st.image(row.image, width="stretch")
            st.markdown(f"**{row.product_name}**")
            st.caption(f"{row.category} | {int(row.units)} units | ${row.sales:,.2f}")

with tab_clusters:
    summary = cluster_summary(filtered)
    st.dataframe(summary, width="stretch", hide_index=True)

    selected_group_for_cluster = st.selectbox("Level 1 group", sorted(filtered["level_1_group"].unique()))
    group_filtered = filtered[filtered["level_1_group"] == selected_group_for_cluster]
    selected_cluster = st.selectbox("Inspect detailed cluster", sorted(group_filtered["cluster"].unique()))
    cluster_rows = group_filtered[group_filtered["cluster"] == selected_cluster]
    cluster_items = items[items["transaction_id"].isin(cluster_rows["transaction_id"])]
    top_products = (
        cluster_items.groupby(["product_name", "category", "image"], as_index=False)
        .agg(units=("quantity", "sum"), sales=("line_total", "sum"))
        .sort_values(["units", "sales"], ascending=False)
        .head(8)
    )

    st.subheader(f"{selected_group_for_cluster} / cluster {selected_cluster} product signals")
    columns = st.columns(4)
    for card_index, row in enumerate(top_products.itertuples(index=False)):
        with columns[card_index % 4]:
            st.image(row.image, width="stretch")
            st.markdown(f"**{row.product_name}**")
            st.caption(f"{row.category} | {int(row.units)} units | ${row.sales:,.2f}")

with tab_transactions:
    selected_transaction = st.selectbox(
        "Transaction detail",
        filtered.sort_values("total", ascending=False)["transaction_id"],
    )
    detail = filtered[filtered["transaction_id"] == selected_transaction].iloc[0]
    st.write(
        {
            "customer_id": detail["customer_id"],
            "level_1_group": detail["level_1_group"],
            "cluster": detail["cluster"],
            "persona": detail["persona"],
            "total": f"${detail['total']:.2f}",
            "aged_total": f"${detail['aged_total']:.2f}",
            "elapsed_months": int(detail["elapsed_months"]),
            "lifecycle_stage": detail["lifecycle_stage"],
            "churn_risk": f"{detail['churn_risk']:.1%}",
            "discount_rate": f"{detail['discount_rate']:.1%}",
            "hour": int(detail["hour"]),
            "loyalty_member": bool(detail["loyalty_member"]),
        }
    )

    selected_items = items[items["transaction_id"] == selected_transaction]
    image_columns = st.columns(min(4, len(selected_items)))
    for image_index, row in enumerate(selected_items.itertuples(index=False)):
        with image_columns[image_index % len(image_columns)]:
            st.image(row.image, width="stretch")
            st.caption(f"{row.product_name} x{row.quantity} - ${row.line_total:.2f}")

    table_columns = [
        "transaction_id",
        "customer_id",
        "level_1_group",
        "persona",
        "cluster",
        "item_count",
        "subtotal",
        "discount_rate",
        "total",
        "aged_total",
        "elapsed_months",
        "lifecycle_stage",
        "churn_risk",
        "recency_weight",
        "hour",
        "weekend",
        "loyalty_member",
        "basket_preview",
    ]
    st.dataframe(filtered[table_columns].sort_values("transaction_id"), width="stretch", hide_index=True)

with tab_catalog:
    st.write("Generated product images used in the simulated transaction baskets.")
    catalog_columns = st.columns(4)
    for catalog_index, product in enumerate(PRODUCTS):
        with catalog_columns[catalog_index % 4]:
            st.image(
                product_image_bytes(product["name"], product["category"], product["color"]),
                width="stretch",
            )
            st.markdown(f"**{product['name']}**")
            st.caption(f"{product['category']} | SKU {product['sku']} | ${product['price']:.2f}")
