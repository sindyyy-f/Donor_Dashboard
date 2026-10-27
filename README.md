# Environmental Nonprofit Donor Engagement & Retention Dashboard

## Project Overview

This dashboard helps an environmental nonprofit monitor donation activity, understand donor engagement, identify donors who may be at risk of disengaging, and forecast future donation growth.

The project uses synthetic donor data and does not contain real names, contact information, payment information, or other personally identifiable information.

## Main Features

The dashboard includes:

- Donor counts, donation counts, the total amount donated, and the average donation amount
- Three compact charts showing campaign totals, monthly donation trends, and donor engagement, with descriptions and visible legends
- Rolling 12-month donor retention below the donation and engagement overview
- A ranked **Donors Needing Attention** table with green row styling and highlighted model risk scores
- An interactive donation forecast covering 3 to 12 months and defaulting to 12 months
- A campaign filter specifically for the forecast
- A -20% to +20% what-if adjustment
- Forecast totals, growth comparisons, different chart views, an optional upper forecast bound, and an optional forecast table
- An environmental theme with trees, an animated river, falling leaves and acorns, and dark-green text
- A full-width footer explaining that all data is synthetically generated

The donor-risk model runs in the background and provides the risk scores shown in the **Donors Needing Attention** table. Its performance cards, confusion matrix, and prediction-count boxes are not displayed on the dashboard. The recent donation records section and general dashboard filters are also not displayed.

## Interactive Donation Forecast

The **Interactive Forecast Controls** section provides:

| Control | Behavior |
|---|---|
| Number of Months to Forecast | Select from 3 to 12 future months; defaults to 12 |
| What-If Donation Adjustment | Adjust the baseline by -20% to +20%; defaults to 0% |
| Campaign | Use all campaigns or rebuild the forecast for one campaign |
| Chart View | Show the baseline, what-if scenario, or both; defaults to both |
| Show Upper Forecast Bound | Toggle the approximate upper bound; visible by default |
| Show Forecast Table | Toggle the monthly forecast table; visible by default |
| Reset Forecast Controls | Restore all defaults using Streamlit session state |

The baseline uses ridge regression with a linear monthly trend and annual seasonal features. Monthly totals include zero-donation months within the observed history. A campaign's history extends to the latest month in the complete dataset, including trailing months with no donations.

At least 18 monthly observations and six months containing donations are required. When a campaign does not have enough data, the application displays a warning instead of producing a forecast.

The final three historical months form a chronological holdout period for Mean Absolute Error (MAE) and Root Mean Squared Error (RMSE) evaluation. The final model is then fitted using all available historical data to generate a cached 12-month baseline forecast.

Changing the selected forecast horizon displays the requested portion of that 12-month baseline. Changing the scenario adjustment does not retrain the model. Selecting a different campaign generates and caches a separate forecast for that campaign.

```text
Adjusted forecast = Baseline forecast * (1 + adjustment percentage / 100)
```

For example, if the baseline forecast is $1,000 and the adjustment is -10%, the adjusted forecast is $900.

Baseline and adjusted totals are compared with actual donations from the immediately preceding equivalent number of months. Growth cannot be calculated when the previous-period total is zero. The selected forecast dates and comparison dates are shown explicitly.

The chart displays:

- Historical actual donations as a solid dark-blue line
- The baseline forecast as a dashed orange line
- The what-if scenario as a dashed green line
- A vertical marker identifying the beginning of the forecast period

The x-axis is labeled **Year-Month**.

The optional forecast table contains:

- Forecast month
- Baseline forecast
- Adjustment percentage
- Adjusted forecast
- Upper forecast bound

No lower forecast bound is displayed or calculated.

The upper bound is an approximate error-based limit derived from the holdout RMSE, and it increases with the forecast horizon. It applies only to the baseline forecast. It is not a calibrated confidence interval or guaranteed limit.

The latest recorded month may be incomplete, which can affect forecast accuracy. All forecasts are academic prototypes based on synthetic data and are not guaranteed financial projections.

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
- Outcome period: November 30, 2025, through August 29, 2026
- Historical training donors: 99
- At-risk training examples: 60
- Not-at-risk training examples: 39

The model studies donor information available on or before the historical snapshot date. It then checks whether each donor made another donation during the following nine-month outcome period.

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

The dashboard calls the model's output a **Model Risk Score**. This score is an estimate produced by the model and is not a guarantee that a donor will become inactive.

## Responsible Use and Limitations

- The project uses synthetic data only.
- Donation forecasts and what-if scenarios are academic estimates, not guaranteed financial projections.
- The model is trained on a small dataset.
- The test set contains only 20 donor examples.
- The model may incorrectly flag active donors as at risk.
- Model results should be reviewed by nonprofit staff.
- Predictions should not be used to make automatic decisions about donors.
- The model does not contact donors or send fundraising messages.
- The project does not process real donations or payment information.
- The forecasting model may be affected by incomplete months or limited campaign history.

## Project Files

| File or Folder | Purpose |
|---|---|
| `app.py` | Runs the dashboard, donor metrics, charts, retention calculations, and attention table |
| `theme.py` | Defines the environmental theme, animated landscape, and section styling |
| `.streamlit/config.toml` | Sets Streamlit colors and readable dark-green text |
| `forecast.py` | Aggregates campaign history, trains monthly forecasts, and calculates scenarios |
| `forecast_ui.py` | Provides cached forecasting, interactive controls, charts, and tables |
| `test_forecast.py` | Tests forecasts, adjustments, filtering, caching, reset behavior, and display behavior |
| `database.py` | Creates the MySQL database connection |
| `model.py` | Builds, evaluates, and applies the donor-risk machine-learning model |
| `analysis.py` | Performs donor analysis, summary calculations, and retention calculations |
| `load_data.py` | Validates and loads synthetic CSV records into MySQL |
| `test_connection.py` | Checks the MySQL connection |
| `test_project.py` | Contains database, data-integrity, and model tests |
| `requirements.txt` | Lists the required Python packages |
| `sql/` | Contains the MySQL database export and supporting data files |
| `.env` | Created locally to store database credentials; excluded from GitHub |

## Setup Instructions

### 1. Download the Project

Clone the GitHub repository or download it as a ZIP file. Open the `Donor_Dashboard` folder in Visual Studio Code.

### 2. Create the Virtual Environment

Open a PowerShell terminal inside the project folder and run:

```powershell
python -m venv .venv
```

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

Run the following commands in MySQL Workbench.

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
DB_PORT=3306
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
.\.venv\Scripts\python.exe -m pytest -q
```

The full test suite contains 33 test cases covering:

- Database connection
- Expected database record counts
- Valid donation amounts
- Valid donor relationships
- Unique donor and donation identifiers
- Valid donor types and campaign values
- Machine-learning training-data integrity
- Machine-learning recall performance target
- Current prediction results
- Forecast horizons and chronological dates
- Zero, positive, and negative scenario adjustments
- Verification that scenario adjustments do not change the baseline
- Nonnegative forecasts and campaign isolation
- Missing donation months and insufficient-data warnings
- Forecast chart views, colors, and upper-bound display
- Cached model reuse, control reset behavior, and forecast-table visibility

Expected result:

```text
33 passed
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
- Forecast dates are chronological.
- Forecast amounts are nonnegative.
- Scenario adjustments do not change the original baseline forecast.

## Security and Privacy

- Only synthetic donor data is used.
- No real donor personally identifiable information is stored.
- Database credentials are kept in the local `.env` file.
- `.env` is excluded from GitHub.
- The application uses a limited MySQL user with read-only access.
- Model predictions are used only as decision-support information.
- Forecasts are estimates and should not be treated as guaranteed financial results.