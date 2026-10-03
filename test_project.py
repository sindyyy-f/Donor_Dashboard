from database import get_connection


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