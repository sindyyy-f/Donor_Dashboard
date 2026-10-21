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
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


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

    donor_features = (
        historical_donations.groupby("donor_id")
        .agg(
            donation_count=("donation_id", "count"),
            total_donated=("donation_amount", "sum"),
            average_donation=("donation_amount", "mean"),
            last_donation_date=("donation_date", "max")
        )
        .reset_index()
    )

    donor_features["days_since_last_donation"] = (
        snapshot_date - donor_features["last_donation_date"]
    ).dt.days

    donor_features = donor_features.merge(
        donors[["donor_id", "donor_type"]],
        on="donor_id",
        how="left"
    )

    future_donors = set(outcome_donations["donor_id"])

    donor_features["at_risk"] = (
        ~donor_features["donor_id"].isin(future_donors)
    ).astype(int)

    return donor_features, snapshot_date, outcome_end


def train_and_evaluate_model(model_data):
    feature_columns = [
        "donation_count",
        "total_donated",
        "average_donation",
        "days_since_last_donation",
        "donor_type"
    ]

    numeric_features = [
        "donation_count",
        "total_donated",
        "average_donation",
        "days_since_last_donation"
    ]

    categorical_features = ["donor_type"]

    X = model_data[feature_columns]
    y = model_data["at_risk"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )

    preprocessing = ColumnTransformer(
        transformers=[
            (
                "numeric",
                StandardScaler(),
                numeric_features
            ),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features
            )
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            (
                "classifier",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=42
                )
            )
        ]
    )

    model.fit(X_train, y_train)

    predictions = model.predict(X_test)

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

    return {
        "model": model,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": matrix,
        "y_test": y_test,
        "predictions": predictions
    }


def main():
    donors, donations = load_database_data()

    model_data, snapshot_date, outcome_end = build_training_data(
        donors,
        donations
    )

    results = train_and_evaluate_model(model_data)

    print("Historical snapshot:", snapshot_date.date())
    print("Outcome period ends:", outcome_end.date())
    print("Training donors:", len(model_data))

    print("\nOutcome classes:")
    print(model_data["at_risk"].value_counts())

    print("\nModel performance:")
    print(f"Accuracy:  {results['accuracy']:.2%}")
    print(f"Precision: {results['precision']:.2%}")
    print(f"Recall:    {results['recall']:.2%}")
    print(f"F1 Score:  {results['f1']:.2%}")

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


if __name__ == "__main__":
    main()