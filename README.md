# Nonprofit Donor Engagement & Retention Dashboard

## Project Overview

The Nonprofit Donor Engagement & Retention Dashboard is a decision-support application designed to help nonprofit staff understand donor activity, donation trends, retention, and possible donor inactivity.

The project uses synthetic donor data and does not contain real names, contact information, payment information, or other personally identifiable information.

## Main Features

The dashboard includes:

- Total number of donors
- Total number of donations
- Total and average donation amounts
- Donations grouped by campaign
- Monthly donation trends
- Rolling 12-month donor retention
- Rule-based donor engagement status
- Machine-learning inactivity-risk predictions
- A ranked list of donors who may need attention
- Recent donation records

## Technology Used

- Python 3.12
- MySQL
- MySQL Workbench
- pandas
- Plotly
- Streamlit
- scikit-learn
- pytest
- Visual Studio Code
- Git and GitHub

## Database

Database name: `donor_dashboard`

The database contains synthetic data for:

- 100 donors
- 400 donation records
- Donor IDs from 1001 through 1100
- Donation IDs from D0001 through D0400
- All 100 donors have at least one donation

### Donors Table

| Field | Description |
|---|---|
| `donor_id` | Unique donor identifier and primary key |
| `donor_type` | Individual, Organization, or Faith Community |
| `join_date` | Date the donor joined |

### Donations Table

| Field | Description |
|---|---|
| `donation_id` | Unique donation identifier and primary key |
| `donor_id` | Foreign key connected to `donors.donor_id` |
| `donation_date` | Date of the donation |
| `donation_amount` | Donation amount |
| `campaign` | Campaign receiving the donation |

The tables have a one-to-many relationship. One donor can have multiple donations, while each donation belongs to one donor.

## Dashboard Calculations

### Engagement Status

The dashboard uses a simple nine-month rule:

- **Active:** The donor donated within the last nine months.
- **At Risk:** The donor has not donated within the last nine months.

This rule is used for the donor engagement chart.

### Donor Retention

Retention is calculated using two rolling 12-month periods.

A retained donor is someone who donated during the previous 12-month period and also donated during the most recent 12-month period.

The current dataset produces:

- Previous 12-month donors: 65
- Retained donors: 40
- Retention rate: 61.5%

## Machine-Learning Model

The project uses logistic regression to identify donors who may be at risk of becoming inactive.

### Historical Evaluation

The model uses:

- Historical snapshot date: November 29, 2025
- Outcome period end date: August 29, 2026
- Historical training donors: 99
- At-risk training examples: 60
- Not-at-risk training examples: 39

The model studies donor information available by the historical snapshot date. It then checks whether each donor made another donation during the following nine months.

### Model Features

The model uses:

- Historical donation count
- Historical total donated
- Historical average donation
- Days since the last donation
- Donations during the previous 12 months
- Amount donated during the previous 12 months
- Donor type

### Model Performance

| Metric | Result |
|---|---:|
| Accuracy | 70.00% |
| Precision | 68.75% |
| Recall | 91.67% |
| F1 score | 78.57% |
| Average five-fold cross-validation recall | 86.67% |

Recall is the primary target metric because the project is designed to avoid missing donors who may be at risk. The target was at least 70% recall, and the model achieved 91.67% recall on the test set.

The model correctly identified 11 of the 12 at-risk donors in the test set.

### Current Predictions

After evaluation, the final model is trained using all 99 historical donor examples and applied to all 100 current donor records.

The current results are:

- Predicted At Risk: 69 donors
- Predicted Not At Risk: 31 donors

The dashboard calls the model’s output a **Model Risk Score**. This score is an estimate produced by the model and is not a guarantee that a donor will become inactive.

## Responsible Use and Limitations

- The project uses synthetic data only.
- The model is trained on a small dataset.
- The test set contains only 20 donor examples.
- The model may incorrectly flag active donors as at risk.
- Model results should be reviewed by nonprofit staff.
- Predictions should not be used to make automatic decisions about donors.
- The model does not contact donors or send fundraising messages.
- The project does not process real donations or payment information.

## Project Files

| File or Folder | Purpose |
|---|---|
| `app.py` | Runs the Streamlit dashboard |
| `database.py` | Creates the MySQL database connection |
| `model.py` | Builds, evaluates, and applies the ML model |
| `analysis.py` | Performs basic donor data analysis |
| `load_data.py` | Loads database data into pandas |
| `test_connection.py` | Checks the MySQL connection |
| `test_project.py` | Contains database, data integrity, and model tests |
| `requirements.txt` | Lists the required Python packages |
| `sql/` | Contains the MySQL database export |
| `.env` | Stores local database credentials and is excluded from GitHub |

## Setup Instructions

### 1. Download the Project

Clone the GitHub repository or download it as a ZIP file. Open the `Donor_Dashboard` folder in Visual Studio Code.

### 2. Create the Virtual Environment

Open a PowerShell terminal inside the project folder and run:

```powershell
python -m venv .venv

The following commands use the virtual environment directly, so activation is not required.

### 3. Install the Required Packages

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Import the MySQL Database

1. Open MySQL Workbench.
2. Connect to the local MySQL server.
3. Select **Server** and then **Data Import**.
4. Select **Import from Self-Contained File**.
5. Choose `sql/donor_dashboard.sql`.
6. Select or create `donor_dashboard` as the target schema.
7. Start the import.

The database should contain 100 donors and 400 donations.

### 5. Create the Application Database User

Run the following in MySQL Workbench. 
Replace `your_password` with a private password:

```sql
CREATE USER IF NOT EXISTS 'capstone_user'@'localhost'
IDENTIFIED BY 'your_password';

GRANT SELECT
ON donor_dashboard.*
TO 'capstone_user'@'localhost';

FLUSH PRIVILEGES;
```

If the user already exists and needs a new password, run:

```sql
ALTER USER 'capstone_user'@'localhost'
IDENTIFIED BY 'your_password';
```

### 6. Create the Environment File

Create a file named `.env` in the main `Donor_Dashboard` folder.

Add:

```text
DB_HOST=localhost
DB_USER=capstone_user
DB_PASSWORD=your_password
DB_NAME=donor_dashboard
```

Replace `your_password` with the password created in MySQL.

The `.env` file is excluded from GitHub to protect the database credentials.

### 7. Test the Database Connection

```powershell
.\.venv\Scripts\python.exe test_connection.py
```

The terminal should confirm that the database connection works.

### 8. Run the Automated Tests

```powershell
.\.venv\Scripts\python.exe -m pytest test_project.py -v
```

The project contains nine automated tests covering:

- Database connection
- Expected database record counts
- Valid donation amounts
- Valid donor relationships
- Unique donor and donation identifiers
- Valid donor types and campaigns
- ML training-data integrity
- ML recall performance target
- Current prediction results

Expected result:

```text
9 passed
```

### 9. Run the Dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit will provide a local address, usually:

```text
http://localhost:8501
```

Open that address in a web browser to use the dashboard.

## Data Integrity Evidence

The automated tests verify that:

- The database contains 100 donors.
- The database contains 400 donations.
- Donation amounts are valid.
- Every donation connects to an existing donor.
- Donor and donation identifiers are unique.
- Donor types and campaign values are valid.
- The model data contains the expected features and no missing feature values.
- Current predictions exist for all 100 donors.
- Model risk scores remain between 0 and 100.

## Security and Privacy

- Only synthetic donor data is used.
- No real donor PII is stored.
- Database credentials are kept in `.env`.
- `.env` is excluded from GitHub.
- The application uses a limited MySQL user with read-only access.
- Model predictions are used only as decision-support information.