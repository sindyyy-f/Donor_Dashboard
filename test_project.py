import pytest

from database import get_connection
from model import (
    FEATURE_COLUMNS,
    build_current_features,
    build_training_data,
    load_database_data,
    predict_current_donor_risk,
    train_and_evaluate_model
)


@pytest.fixture(scope="module")
def model_bundle():
    donors, donations = load_database_data()

    training_data, snapshot_date, outcome_end = (
        build_training_data(
            donors,
            donations
        )
    )

    results = train_and_evaluate_model(
        training_data
    )

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

    return {
        "donors": donors,
        "donations": donations,
        "training_data": training_data,
        "results": results,
        "current_predictions": current_predictions,
        "snapshot_date": snapshot_date,
        "outcome_end": outcome_end,
        "prediction_date": prediction_date
    }


def test_database_connection():
    connection = get_connection()

    assert connection.is_connected()

    connection.close()


def test_database_record_counts():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM donors")
    donor_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM donations")
    donation_count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    assert donor_count == 100
    assert donation_count == 400


def test_donation_amounts_are_valid():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM donations
        WHERE donation_amount IS NULL
           OR donation_amount <= 0
        """
    )

    invalid_amounts = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    assert invalid_amounts == 0


def test_every_donation_has_a_donor():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM donations AS dn
        LEFT JOIN donors AS dr
            ON dn.donor_id = dr.donor_id
        WHERE dr.donor_id IS NULL
        """
    )

    donations_without_donors = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    assert donations_without_donors == 0


def test_identifiers_are_unique():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*) - COUNT(DISTINCT donor_id)
        FROM donors
        """
    )

    duplicate_donors = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT
            COUNT(*) - COUNT(DISTINCT donation_id)
        FROM donations
        """
    )

    duplicate_donations = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    assert duplicate_donors == 0
    assert duplicate_donations == 0


def test_categories_are_valid():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM donors
        WHERE donor_type IS NULL
           OR donor_type NOT IN (
               'Individual',
               'Organization',
               'Faith Community'
           )
        """
    )

    invalid_donor_types = cursor.fetchone()[0]

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM donations
        WHERE campaign IS NULL
           OR TRIM(campaign) = ''
        """
    )

    invalid_campaigns = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    assert invalid_donor_types == 0
    assert invalid_campaigns == 0


def test_model_training_data(model_bundle):
    training_data = model_bundle["training_data"]

    assert len(training_data) == 99

    assert set(
        training_data["at_risk"].unique()
    ) == {0, 1}

    assert (
        training_data["at_risk"].value_counts()[1]
        == 60
    )

    assert (
        training_data["at_risk"].value_counts()[0]
        == 39
    )

    for feature in FEATURE_COLUMNS:
        assert feature in training_data.columns

    assert not training_data[
        FEATURE_COLUMNS
    ].isnull().any().any()


def test_model_meets_recall_target(model_bundle):
    results = model_bundle["results"]

    test_recall = results["recall"]

    average_cv_recall = (
        results["cv_recall_scores"].mean()
    )

    assert test_recall >= 0.70
    assert average_cv_recall >= 0.70


def test_current_model_predictions(model_bundle):
    predictions = model_bundle[
        "current_predictions"
    ]

    assert len(predictions) == 100

    assert predictions["donor_id"].nunique() == 100

    assert set(
        predictions["ml_prediction"].unique()
    ).issubset(
        {"At Risk", "Not At Risk"}
    )

    assert predictions[
        "risk_probability"
    ].between(0, 100).all()

    assert not predictions.isnull().any().any()