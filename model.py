import pandas as pd

from database import get_connection
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    train_test_split
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


FEATURE_COLUMNS = [
    "donation_count",
    "total_donated",
    "average_donation",
    "days_since_last_donation",
    "donations_last_12_months",
    "amount_last_12_months",
    "donor_type"
]

NUMERIC_FEATURES = [
    "donation_count",
    "total_donated",
    "average_donation",
    "days_since_last_donation",
    "donations_last_12_months",
    "amount_last_12_months"
]

CATEGORICAL_FEATURES = ["donor_type"]


def load_database_data():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM donors")
    donors = pd.DataFrame(cursor.fetchall())

    cursor.execute("SELECT * FROM donations")
    donations = pd.DataFrame(cursor.fetchall())

    cursor.close()
    connection.close()

    donations["donation_date"] = pd.to_datetime(
        donations["donation_date"]
    )

    donations["donation_amount"] = pd.to_numeric(
        donations["donation_amount"]
    )

    return donors, donations


def build_donor_features(
    donors,
    available_donations,
    reference_date
):
    donor_features = (
        available_donations.groupby("donor_id")
        .agg(
            donation_count=("donation_id", "count"),
            total_donated=("donation_amount", "sum"),
            average_donation=("donation_amount", "mean"),
            last_donation_date=("donation_date", "max")
        )
        .reset_index()
    )

    donor_features["days_since_last_donation"] = (
        reference_date - donor_features["last_donation_date"]
    ).dt.days

    recent_period_start = (
        reference_date - pd.DateOffset(months=12)
    )

    recent_donations = available_donations[
        (
            available_donations["donation_date"]
            >= recent_period_start
        )
        & (
            available_donations["donation_date"]
            <= reference_date
        )
    ].copy()

    recent_features = (
        recent_donations.groupby("donor_id")
        .agg(
            donations_last_12_months=(
                "donation_id",
                "count"
            ),
            amount_last_12_months=(
                "donation_amount",
                "sum"
            )
        )
        .reset_index()
    )

    donor_features = donor_features.merge(
        recent_features,
        on="donor_id",
        how="left"
    )

    donor_features[
        [
            "donations_last_12_months",
            "amount_last_12_months"
        ]
    ] = donor_features[
        [
            "donations_last_12_months",
            "amount_last_12_months"
        ]
    ].fillna(0)

    donor_features = donor_features.merge(
        donors[["donor_id", "donor_type"]],
        on="donor_id",
        how="left"
    )

    return donor_features


def build_training_data(donors, donations):
    outcome_end = donations["donation_date"].max()

    snapshot_date = (
        outcome_end - pd.DateOffset(months=9)
    )

    historical_donations = donations[
        donations["donation_date"] <= snapshot_date
    ].copy()

    outcome_donations = donations[
        (donations["donation_date"] > snapshot_date)
        & (donations["donation_date"] <= outcome_end)
    ].copy()

    donor_features = build_donor_features(
        donors,
        historical_donations,
        snapshot_date
    )

    future_donors = set(outcome_donations["donor_id"])

    donor_features["at_risk"] = (
        ~donor_features["donor_id"].isin(future_donors)
    ).astype(int)

    return donor_features, snapshot_date, outcome_end


def build_current_features(donors, donations):
    prediction_date = donations["donation_date"].max()

    current_features = build_donor_features(
        donors,
        donations,
        prediction_date
    )

    return current_features, prediction_date


def create_model_pipeline():
    preprocessing = ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                NUMERIC_FEATURES
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES
            )
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight={0: 1, 1: 1.5},
                    random_state=42
                )
            )
        ]
    )


def train_and_evaluate_model(model_data):
    X = model_data[FEATURE_COLUMNS]
    y = model_data["at_risk"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    evaluation_model = create_model_pipeline()

    cross_validation = StratifiedKFold(
        n_splits=5,
        shuffle=True,
        random_state=42
    )

    cv_recall_scores = cross_val_score(
        evaluation_model,
        X,
        y,
        cv=cross_validation,
        scoring="recall"
    )

    evaluation_model.fit(X_train, y_train)

    predictions = evaluation_model.predict(X_test)

    accuracy = accuracy_score(y_test, predictions)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=[0, 1]
    )

    # Train the final model using all 99 historical donors
    final_model = create_model_pipeline()
    final_model.fit(X, y)

    return {
        "model": final_model,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": matrix,
        "y_test": y_test,
        "predictions": predictions,
        "cv_recall_scores": cv_recall_scores
    }


def predict_current_donor_risk(
    trained_model,
    current_features
):
    prediction_values = trained_model.predict(
        current_features[FEATURE_COLUMNS]
    )

    prediction_probabilities = (
        trained_model.predict_proba(
            current_features[FEATURE_COLUMNS]
        )[:, 1]
    )

    current_predictions = current_features[
        [
            "donor_id",
            "donor_type",
            "last_donation_date",
            "days_since_last_donation",
            "donation_count",
            "donations_last_12_months"
        ]
    ].copy()

    current_predictions["risk_probability"] = (
        prediction_probabilities * 100
    ).round(1)

    current_predictions["ml_prediction"] = [
        "At Risk" if value == 1 else "Not At Risk"
        for value in prediction_values
    ]

    current_predictions = current_predictions.sort_values(
        "risk_probability",
        ascending=False
    )

    return current_predictions


def main():
    donors, donations = load_database_data()

    model_data, snapshot_date, outcome_end = (
        build_training_data(
            donors,
            donations
        )
    )

    results = train_and_evaluate_model(model_data)

    current_features, prediction_date = (
        build_current_features(
            donors,
            donations
        )
    )

    current_predictions = predict_current_donor_risk(
        results["model"],
        current_features
    )

    print("Historical snapshot:", snapshot_date.date())
    print("Outcome period ends:", outcome_end.date())
    print("Training donors:", len(model_data))

    print("\nModel performance:")
    print(f"Accuracy:  {results['accuracy']:.2%}")
    print(f"Precision: {results['precision']:.2%}")
    print(f"Recall:    {results['recall']:.2%}")
    print(f"F1 Score:  {results['f1']:.2%}")

    print("\nFive-fold cross-validation recall:")

    for fold_number, score in enumerate(
        results["cv_recall_scores"],
        start=1
    ):
        print(f"Fold {fold_number}: {score:.2%}")

    print(
        "Average recall:",
        f"{results['cv_recall_scores'].mean():.2%}"
    )

    print("\nConfusion matrix:")
    print(results["confusion_matrix"])

    print("\nClassification report:")

    print(
        classification_report(
            results["y_test"],
            results["predictions"],
            labels=[0, 1],
            target_names=["Not At Risk", "At Risk"],
            zero_division=0
        )
    )

    print("Current prediction date:", prediction_date.date())

    print("\nCurrent prediction counts:")
    print(
        current_predictions[
            "ml_prediction"
        ].value_counts()
    )

    print("\nTen highest predicted risks:")
    print(
        current_predictions[
            [
                "donor_id",
                "donor_type",
                "risk_probability",
                "ml_prediction"
            ]
        ].head(10).to_string(index=False)
    )


if __name__ == "__main__":
    main()