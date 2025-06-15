# LangGraph Cross-Sell/Upsell Recommendation Agent

This project implements a modular LangGraph agent designed to analyze customer purchase data, identify cross-sell and upsell opportunities, and generate detailed natural-language research reports. The solution leverages Google's Gemini-1.5-flash-latest LLM, uses PostgreSQL for data storage, and is fully containerized using Docker Compose for easy deployment and management.

## Table of Contents

1.  [Features](#1-features)
2.  [Project Structure](#2-project-structure)
3.  [Prerequisites](#3-prerequisites)
4.  [Setup & Installation](#4-setup--installation)
    *   [Environment Variables (`.env`)](#environment-variables-env)
    *   [Data Preparation (`init.sql`)](#data-preparation-initsql)
    *   [Initial Database Setup](#initial-database-setup)
5.  [Running the Application](#5-running-the-application)
6.  [API Usage](#6-api-usage)
7.  [Agent Pipeline Overview](#7-agent-pipeline-overview)

---

## 1. Features

*   **Modular LangGraph Agent**: Orchestrates a series of specialized sub-agents for distinct analysis steps.
*   **Customer Context Agent**: Extracts detailed customer profiles and purchase histories from PostgreSQL.
*   **Purchase Pattern Analysis**: Identifies frequent purchases and "missing opportunities" by benchmarking against industry peers.
*   **Product Affinity Analysis**: Suggests related products based on co-occurrence patterns across the entire dataset.
*   **Opportunity Scoring**: Scores potential cross-sell and upsell products based on combined insights.
*   **Recommendation Report Generation**: Leverages Gemini LLM to synthesize insights into a comprehensive, structured natural-language report and extract actionable recommendations.
*   **FastAPI REST API**: Exposes the agent pipeline via a simple HTTP endpoint.
*   **PostgreSQL Integration**: Data is stored and retrieved from a PostgreSQL database.
*   **Dockerization**: Provides a portable and isolated development/production environment using Docker and Docker Compose.
*   **Configurable LLM**: Easily switch between different Gemini models via environment variables.

---

## 2. Project Structure
.
├── .env # Environment variables for API keys and DB credentials
├── main.py # Main FastAPI application and LangGraph agent definitions
├── db_manager.py # Handles PostgreSQL database connection and queries
├── init.sql # SQL script for table creation and initial data insertion
├── customer_data.csv # Source CSV data used to generate init.sql
├── generateinit.py # Python script to convert customer_data.csv to init.sql
├── Dockerfile # Defines the Docker image for the FastAPI application
├── requirements.txt # Python dependencies
└── docker-compose.yml # Orchestrates the application and PostgreSQL database containers


---

## 3. Prerequisites

Before running the application, ensure you have the following installed:

*   **Docker**: [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose) or Docker Engine and Docker Compose standalone.
*   **Git** (optional, for cloning this repository).
*   **Google Cloud Account**: To obtain a `GOOGLE_API_KEY` for accessing the Gemini API. Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

---

## 4. Setup & Installation

Follow these steps to get the application running:

### Environment Variables (`.env`)

Create a `.env` file in the root directory of the project with the following content. Replace placeholders with your actual values:

```env
GOOGLE_API_KEY="YOUR_GOOGLE_GEMINI_API_KEY_HERE"
LLM_MODEL="gemini-1.5-flash-latest" # Or gemini-1.5-pro-latest

DB_HOST="db"
DB_NAME="customer_db"
DB_USER="user"
DB_PASSWORD="password"
```
### Data Preparation (`init.sql`)

The `init.sql` file contains the SQL DDL (Data Definition Language) for creating the `customer_purchases` table and DML (Data Manipulation Language) for inserting sample data. This data is derived from `customer_data.csv`.

1.  **Ensure `customer_data.csv` is present:**
    Make sure `customer_data.csv` is in the project root directory. It should contain the raw customer purchase data as provided in the assignment, ensuring all string fields are enclosed in double quotes for robust parsing.

2.  **Generate `init.sql`:**
    Run the `generateinit.py` script to create or update `init.sql`. This script includes logic to `DROP TABLE IF EXISTS` for clean database re-initialization.

    ```bash
    python3 generateinit.py
    ```

### Initial Database Setup

It's crucial to ensure the PostgreSQL database is initialized correctly with data. If you've run `docker compose up` before and did not explicitly remove volumes, PostgreSQL might skip initialization.

1.  **Stop and remove any previous containers and volumes:**
    ```bash
    docker compose down -v
    ```
    The `-v` flag is essential as it removes the named volume (`pg_data`) where PostgreSQL persists its data, forcing a fresh initialization on the next `up`.

---

## 5. Running the Application

After completing the setup steps:

1.  **Build and start the Docker containers:**
    Navigate to the project's root directory in your terminal and run:

    ```bash
    docker compose up --build
    ```
    *   `--build`: Ensures your Docker images are rebuilt, picking up any changes in `Dockerfile` or `main.py`.
    *   This command will:
        *   Build the FastAPI application's Docker image.
        *   Start the PostgreSQL database container.
        *   Execute `init.sql` inside the database container to create the table and populate data.
        *   Start the FastAPI application container, configured to wait for the database to become healthy.

2.  **Verify container status:**
    You can check if both containers are running using:
    ```bash
    docker compose ps
    ```
    You should see `app` and `db` services in a `running` or `healthy` state.

---

## 6. API Usage

The FastAPI application will be accessible at `http://localhost:8000`.

*   **Endpoint:** `GET /recommendation/{customer_id}`

*   **Function:** Runs the LangGraph agent pipeline for the specified `customer_id`, returning a comprehensive research report and structured recommendations.

*   **Example Requests:**

    *   For customer `C001`: `http://localhost:8000/recommendation/C001`
    *   For customer `C003`: `http://localhost:8000/recommendation/C003`
    *   For a non-existent customer (e.g., `C999`): `http://localhost:8000/recommendation/C999` (will return a `404 Not Found` error).

*   **Expected JSON Response Structure:**

    ```json
    {
      "customer_id": "C001",
      "research_report": "Research Report: Cross-Sell and Upsell Opportunities for Edge Communications...\n\nIntroduction: ...\n\nCustomer Overview: ...\n\nData Analysis: ...\n\nRecommendations: ...\n\nConclusion: ...",
      "recommendations": [
        {
          "product": "Backup Batteries",
          "type": "Upsell",
          "reason": "Customer already purchases items in the 'Power Tools & Equipment' category, suggesting an upsell. Many peers in 'Electronics' industry purchase 'Backup Batteries'. Frequently co-purchased with 'Generators' (multiple times by other customers)."
        },
        {
          "product": "Safety Gear",
          "type": "Cross-Sell",
          "reason": "Product is in a new category ('Safety & Apparel'), indicating a cross-sell opportunity. Many peers in 'Electronics' industry purchase 'Safety Gear'. Frequently co-purchased with 'Drill Bits' (multiple times by other customers)."
        }
        // ... (up to 5 top recommendations based on scoring)
      ],
      "error": null
    }
    ```
    The `research_report` content will vary based on the LLM's generation but will follow the specified structure.

---

## 7. Agent Pipeline Overview

The LangGraph pipeline orchestrates the following sub-agents:

| Agent Name                     | Purpose                                                              | Input              | Output                                     |
| :----------------------------- | :------------------------------------------------------------------- | :----------------- | :----------------------------------------- |
| **Customer Context Agent**     | Extracts customer profile and purchase history from PostgreSQL.      | `customer_id`      | `customer_profile`, `customer_purchase_history` |
| **Purchase Pattern Analysis**  | Identifies product purchase frequency and missing opportunities (from peers). | `customer_profile`, `customer_purchase_history` | `frequent_products`, `missing_opportunities_products` |
| **Product Affinity Agent**     | Suggests related/co-purchased products across all customers.         | `frequent_products` | `related_product_suggestions`              |
| **Opportunity Scoring Agent**  | Scores cross-sell and upsell opportunities with rationale.           | `customer_profile`, `frequent_products`, `missing_opportunities_products`, `related_product_suggestions` | `scored_opportunities`                     |
| **Recommendation Report Agent** | Generates a natural-language research report & structured recommendations using LLM. | All prior agent data, `scored_opportunities` | `research_report`, `recommendations_structured` |

The graph flow is sequential: `Customer Context` -> `Purchase Pattern Analysis` -> `Product Affinity` -> `Opportunity Scoring` -> `Recommendation Report` -> `END`. A conditional edge handles `customer_id` not found errors after the `Customer Context Agent`.
