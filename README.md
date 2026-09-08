# Donor_Dashboard
MySQL Workbench 

Database
Database name: donor_dashboard

Dataset
- 100 synthetic donors
- 400 synthetic donation records
- All 100 donors have at least one donation record
- Donor IDs range from 1001 through 1100
- Donation IDs range from D0001 through D0400
- No real donor personally identifiable information is included

Table 1: donors
- donor_id: Unique donor identifier and primary key
- donor_type: Individual, Organization, or Faith Community
- join_date: Date the donor joined

Table 2: donations
- donation_id: Unique donation identifier and primary key
- donor_id: Foreign key connected to donors.donor_id
- donation_date: Date of the donation
- donation_amount: Donation amount
- campaign: Campaign that received the donation

Relationship
The donors and donations tables have a one-to-many relationship. One donor can have multiple donations, while each donation belongs to one donor. The tables are connected through donor_id.

Donor Summary View
The donor_summary view combines data from both tables and calculates:
- Donation count
- Total donated
- Average donation amount
- First donation date
- Last donation date
- Days since the last donation
- Active or Inactive status

Status Rule
- Reference date: 2026-09-01
- Active: At least one donation during the previous 365 days
- Inactive: No donation during the previous 365 days

Validation Queries
Run these queries in MySQL Workbench to verify the final database:

SELECT COUNT(*) AS donor_count FROM donors;
Expected result: 100

SELECT COUNT(*) AS donation_count FROM donations;
Expected result: 400

SELECT COUNT(DISTINCT donor_id) AS donors_with_donations FROM donations;
Expected result: 100

SELECT * FROM donor_summary LIMIT 10;
