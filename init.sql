-- init.sql
DROP TABLE IF EXISTS customer_purchases;
CREATE TABLE customer_purchases (
    "Customer ID" VARCHAR(50),
    "Product" VARCHAR(100),
    "Quantity" INTEGER,
    "Unit Price (USD)" NUMERIC,
    "Total Price (USD)" NUMERIC,
    "Purchase Date" DATE,
    "Customer Name" VARCHAR(255),
    "Industry" VARCHAR(100),
    "Annual Revenue (USD)" NUMERIC,
    "Number of Employees" INTEGER,
    "Customer Priority Rating" VARCHAR(50),
    "Account Type" VARCHAR(50),
    "Location" VARCHAR(255),
    "Current Products" VARCHAR(255),
    "Product Usage (%)" NUMERIC,
    "Cross-Sell Synergy" VARCHAR(255),
    "Last Activity Date" DATE,
    "Opportunity Stage" VARCHAR(100)
);

-- Insert sample data
INSERT INTO customer_purchases VALUES ('C001','Drill Bits',9,250.0,2250.0,'2024-11-27','Edge Communications','Electronics',139000000.0,1000,'Medium','Customer - Direct','Austin, TX, USA','Core Management Platform',100.0,'Collaboration Suite,E','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C001','Protective Gloves',9,1000.0,9000.0,'2024-10-23','Edge Communications','Electronics',139000000.0,1000,'Medium','Customer - Direct','Austin, TX, USA','Core Management Platform',100.0,'Collaboration Suite,E','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C001','Generators',1,1000.0,1000.0,'2024-09-27','Edge Communications','Electronics',139000000.0,1000,'Medium','Customer - Direct','Austin, TX, USA','Core Management Platform',100.0,'Collaboration Suite,E','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C001','Drill Bits',6,750.0,4500.0,'2025-05-31','Edge Communications','Electronics',139000000.0,1000,'Medium','Customer - Direct','Austin, TX, USA','Core Management Platform',100.0,'Collaboration Suite,E','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C001','Workflow Automation',1,500.0,500.0,'2024-07-11','Edge Communications','Electronics',139000000.0,1000,'Medium','Customer - Direct','Austin, TX, USA','Core Management Platform',100.0,'Collaboration Suite,E','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C001','Generators',4,100.0,400.0,'2025-05-10','Edge Communications','Electronics',139000000.0,1000,'Medium','Customer - Direct','Austin, TX, USA','Core Management Platform',100.0,'Collaboration Suite,E','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C001','Protective Gloves',1,100.0,100.0,'2024-11-27','Edge Communications','Electronics',139000000.0,1000,'Medium','Customer - Direct','Austin, TX, USA','Core Management Platform',100.0,'Collaboration Suite,E','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C001','Workflow Automation',10,500.0,5000.0,'2025-05-08','Edge Communications','Electronics',139000000.0,1000,'Medium','Customer - Direct','Austin, TX, USA','Core Management Platform',100.0,'Collaboration Suite,E','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Drills',4,100.0,400.0,'2024-06-10','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Backup Batteries',9,100.0,900.0,'2024-06-15','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Backup Batteries',8,750.0,6000.0,'2024-10-20','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Protective Gloves',4,1000.0,4000.0,'2024-10-11','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Generators',7,250.0,1750.0,'2025-03-18','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Workflow Automation',9,1000.0,6000.0,'2025-05-18','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Drills',2,250.0,500.0,'2024-10-06','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Drill Bits',6,1000.0,9000.0,'2025-04-17','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','API Integrations',1,500.0,500.0,'2024-06-26','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Collaboration Suite',5,250.0,1250.0,'2024-06-16','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Backup Batteries',7,500.0,3500.0,'2024-11-30','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Workflow Automation',8,1000.0,8000.0,'2024-06-27','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Safety Gear',1,750.0,750.0,'2025-02-07','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C002','Workflow Automation',1,750.0,750.0,'2025-01-19','Burlington Textiles Corp','Apparel',350000000.0,9000,'High','Customer-Direct','Burlington, NC, USA','Collaboration Suite',85.0,'Advanced Analytics,F','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C003','Protective Gloves',2,750.0,1500.0,'2025-03-22','Pyramid Construction Inc.','Construction',950000000.0,2680,'High','Customer-Channel','Paris, France','Advanced Analytics',70.0,'Workflow Automation,G','2024-11-19','Prospecting');
INSERT INTO customer_purchases VALUES ('C003','API Integrations',5,750.0,3750.0,'2024-06-27','Pyramid Construction Inc.','Construction',950000000.0,2680,'High','Customer-Channel','Paris, France','Advanced Analytics',70.0,'Workflow Automation,G','2024-11-19','Prospecting');
INSERT INTO customer_purchases VALUES ('C003','Advanced Analytics',6,750.0,4500.0,'2024-07-07','Pyramid Construction Inc.','Construction',950000000.0,2680,'High','Customer-Channel','Paris, France','Advanced Analytics',70.0,'Workflow Automation,G','2024-11-19','Prospecting');
INSERT INTO customer_purchases VALUES ('C003','API Integrations',9,1000.0,9000.0,'2024-10-29','Pyramid Construction Inc.','Construction',950000000.0,2680,'High','Customer-Channel','Paris, France','Advanced Analytics',70.0,'Workflow Automation,G','2024-11-19','Prospecting');
INSERT INTO customer_purchases VALUES ('C003','Safety Gear',10,100.0,1000.0,'2025-03-28','Pyramid Construction Inc.','Construction',950000000.0,2680,'High','Customer-Channel','Paris, France','Advanced Analytics',70.0,'Workflow Automation,G','2024-11-19','Prospecting');
INSERT INTO customer_purchases VALUES ('C003','Workflow Automation',6,250.0,1500.0,'2024-12-17','Pyramid Construction Inc.','Construction',950000000.0,2680,'High','Customer-Channel','Paris, France','Advanced Analytics',70.0,'Workflow Automation,G','2024-11-19','Prospecting');
INSERT INTO customer_purchases VALUES ('C004','Advanced Analytics',8,250.0,2000.0,'2024-07-10','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Backup Batteries',6,500.0,4500.0,'2024-10-07','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Backup Batteries',6,250.0,2250.0,'2024-12-26','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Safety Gear',10,1000.0,10000.0,'2024-11-24','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Protective Gloves',2,500.0,1000.0,'2024-11-13','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Drill Bits',6,100.0,600.0,'2024-09-04','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Generators',5,1000.0,5000.0,'2024-12-12','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Safety Gear',8,100.0,800.0,'2025-01-01','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Backup Batteries',8,100.0,800.0,'2025-04-02','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Generators',8,100.0,800.0,'2024-11-08','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Generators',6,750.0,4500.0,'2024-11-19','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','Generators',3,100.0,300.0,'2025-01-26','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C004','API Integrations',9,1000.0,6000.0,'2025-02-28','Grand Hotels & Resorts','Hospitality',500000000.0,5600,'High','Customer Direct','Chicago, IL, USA','Reporting Dashboard',65.0,'API Integrations,H','2024-11-19','Closed Won');
INSERT INTO customer_purchases VALUES ('C005','Generators',5,250.0,1250.0,'2025-03-25','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer-Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
INSERT INTO customer_purchases VALUES ('C005','Workflow Automation',5,500.0,2500.0,'2024-09-25','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
INSERT INTO customer_purchases VALUES ('C005','Safety Gear',3,100.0,300.0,'2025-01-01','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer-Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
INSERT INTO customer_purchases VALUES ('C005','Drills',2,750.0,1500.0,'2024-11-06','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
INSERT INTO customer_purchases VALUES ('C005','Safety Gear',9,250.0,2250.0,'2024-12-04','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer - Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
INSERT INTO customer_purchases VALUES ('C005','Collaboration Suite',9,500.0,4500.0,'2025-01-20','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer-Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
INSERT INTO customer_purchases VALUES ('C005','Workflow Automation',2,250.0,500.0,'2024-12-03','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer-Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
INSERT INTO customer_purchases VALUES ('C005','Collaboration Suite',2,250.0,500.0,'2024-07-25','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer - Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
INSERT INTO customer_purchases VALUES ('C005','API Integrations',8,1000.0,8000.0,'2024-09-07','United Oil & Gas Corp.','Energy',5600000000.0,145000,'High','Customer - Direct','New York, NY, USA','Workflow Automation',60.0,'AI Insights Module,J','2024-11-19','Negotiation/Review');
