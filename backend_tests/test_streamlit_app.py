from __future__ import annotations

import runpy
from pathlib import Path

import numpy as np
import pytest

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def test_streamlit_default_render_and_empty_filter_state() -> None:
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(APP_PATH)
    app.run(timeout=30)

    assert not app.exception
    assert app.title[0].value == "Asterism Store Purchase Cluster Simulation"
    assert [slider.label for slider in app.slider] == [
        "Test transactions",
        "Clusters",
        "History window months",
        "Simulation age month",
    ]
    assert app.number_input[0].label == "Random seed"
    assert app.radio[0].label == "Map color"
    assert app.toggle[0].label == "Show chart grid"
    assert app.multiselect[0].label == "Filter personas"
    assert [metric.label for metric in app.metric] == [
        "Transactions",
        "Aged revenue",
        "Avg aged basket",
        "Avg age",
    ]
    assert len(app.dataframe) >= 4
    assert len(app.image) >= 16

    empty = AppTest.from_file(APP_PATH)
    empty.run(timeout=30)
    empty.multiselect[0].set_value([])
    empty.run(timeout=30)

    assert not empty.exception
    assert empty.warning[0].value == "Select at least one persona to show clustered purchase simulations."


def test_streamlit_simulation_pipeline_invariants() -> None:
    pytest.importorskip("streamlit")
    module = runpy.run_path(str(APP_PATH))

    products = module["PRODUCTS"]
    category_order = module["CATEGORY_ORDER"]
    build_transactions = module["build_transactions"]
    age_transactions = module["age_transactions"]
    cluster_transactions = module["cluster_transactions"]
    cluster_summary = module["cluster_summary"]
    product_image_bytes = module["product_image_bytes"]
    standardize = module["standardize"]
    kmeans = module["kmeans"]
    pca_3d = module["pca_3d"]

    assert len(products) == 16
    assert category_order == sorted({product["category"] for product in products})
    image = product_image_bytes("Organic Apples", "Produce", "#2f9e44")
    assert image.startswith(b"\x89PNG")
    assert len(image) > 1000

    transactions, items = build_transactions(80, 127, 6)
    assert len(transactions) == 80
    assert set(transactions["transaction_id"]).issubset(set(items["transaction_id"]))
    assert transactions["total"].gt(0).all()
    assert items["line_total"].gt(0).all()
    assert items["image"].map(lambda value: value.startswith(b"\x89PNG")).all()

    aged0 = age_transactions(transactions, 0)
    aged6 = age_transactions(transactions, 6)
    assert aged0["elapsed_months"].eq(0).all()
    assert aged6["churn_risk"].between(0.03, 0.92).all()

    clustered = cluster_transactions(aged6, 4)
    assert len(clustered) == 80
    assert {"level_1_group", "cluster", "x", "y", "z"} <= set(clustered.columns)
    assert clustered["cluster"].nunique() <= 4
    assert np.isfinite(clustered[["x", "y", "z"]].to_numpy()).all()

    summary = cluster_summary(clustered)
    assert summary["transactions"].sum() == 80
    assert standardize(np.ones((4, 3))).shape == (4, 3)
    assert len(kmeans(np.arange(20).reshape(10, 2).astype(float), 3, seed=1)) == 10
    assert pca_3d(np.arange(4).reshape(2, 2).astype(float)).shape == (2, 3)
