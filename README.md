# Nonprofit Donor Engagement & Retention Dashboard

## Project Overview

This project is a Streamlit dashboard designed to help nonprofit staff understand donor activity, engagement, and retention. It connects Python to a MySQL database containing synthetic donor and donation records.

The project uses fictional data only. It does not contain real donor names, contact information, payment information, or other personally identifiable information.

## Sprint 1 Features

The current Sprint 1 build includes:

- A MySQL database containing donor and donation records
- A secure Python connection to MySQL
- Data analysis using pandas
- Four summary metrics
- Donation totals by campaign
- Monthly donation trends for the most recent year
- Donor engagement classification
- An at-risk donor table
- Rolling 12-month donor retention metrics
- Automated database and data-quality tests
- Version control through Git and GitHub

## Technology Stack

- Python
- MySQL
- MySQL Workbench
- pandas
- Plotly
- Streamlit
- pytest
- Git and GitHub
- Visual Studio Code

## Database

Database name:

```text
donor_dashboard
```

### Dataset

- 100 synthetic donors
- 400 synthetic donation records
- All 100 donors have at least one donation record
- Donor IDs range from `1001` through `1100`
- Donation IDs range from `D0001` through `D0400`

### Donors Table

| Column | Description |
|---|---|
| `donor_id` | Unique donor identifier and primary key |
| `donor_type` | Individual, Organization, or Faith Community |
| `join_date` | Date the donor joined |

### Donations Table

| Column | Description |
|---|---|
| `donation_id` | Unique donation identifier and primary key |
| `donor_id` | Foreign key connected to `donors.donor_id` |
| `donation_date` | Date of the donation |
| `donation_amount` | Donation amount |
| `campaign` | Campaign that received the donation |

### Database Relationship

The `donors` and `donations` tables have a one-to-many relationship. One donor can make multiple donations, while each donation belongs to one donor. The tables are connected through `donor_id`.

### Donor Summary View

The `donor_summary` view combines and summarizes information from the two database tables. It includes values such as:

- Donation count
- Total donated
- Average donation amount
- First donation date
- Most recent donation date
- Days since the most recent donation

## Dashboard Metrics

The dashboard displays:

- Total donors
- Number of donations
- Total amount donated
- Average donation amount
- Previous-period donors
- Retained donors
- Rolling 12-month retention rate
- Number of at-risk donors

## Engagement Rule

- **Active:** The donor has donated within the last nine months.
- **At Risk:** The donor has not donated within the last nine months.

The engagement calculation uses each donor's most recent donation date. The result is intended to support staff decisions and is not a guaranteed prediction of future behavior.

## Retention Calculation

Retention is calculated using two rolling 12-month periods:

1. The most recent 12-month period in the dataset
2. The 12-month period immediately before it

A donor is retained if the donor made at least one donation during both periods.

```text
Retention Rate = Retained Donors / Previous-Period Donors × 100
```

The current Sprint 1 dataset contains:

- 65 previous-period donors
- 40 retained donors
- 61.5% retention rate

## Project Setup

### 1. Create a Virtual Environment

```text
python -m venv .venv
```

### 2. Activate the Virtual Environment

Using Windows Command Prompt:

```text
.venv\Scripts\activate.bat
```

### 3. Install the Required Packages

```text
python -m pip install -r requirements.txt
```

### 4. Set Up the Database

Open and run the following file in MySQL Workbench:

```text
sql/donor_dashboard.sql
```

### 5. Create the Environment File

Create a file named `.env` in the main project folder:

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=capstone_user
DB_PASSWORD=your_database_password
DB_NAME=donor_dashboard
```

The `.env` file is excluded from GitHub and should never be committed.

### 6. Run the Dashboard

```text
python -m streamlit run app.py
```

## Testing

Run the Sprint 1 automated tests with:

```text
python -m pytest test_project.py -v
```

The tests verify:

- Python can connect to MySQL
- The database contains 100 donors
- The database contains 400 donations
- Donation amounts are present and greater than zero
- Every donation belongs to an existing donor

The expected result is:

```text
4 passed
```

## Security and Privacy

- All donor and donation records are synthetic.
- No real donor PII is stored.
- Database credentials are stored in `.env`.
- The `.env` file is excluded from GitHub.
- The application uses a limited MySQL user with read-only access.
- Dashboard results are intended for decision support only.

## Planned Sprint 2 Work

- Develop and evaluate one simple machine-learning model
- Compare model results with the rule-based engagement calculation
- Improve dashboard usability
- Complete additional testing
- Prepare the application for cloud deployment