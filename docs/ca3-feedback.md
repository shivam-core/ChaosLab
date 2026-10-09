# CA3 Feedback and Implementation Evidence

| Professor Feedback | Implemented Response | Evidence | Status |
| :--- | :--- | :--- | :--- |
| "Prototype too abstract" | Switched from generic "orders" to a full Retail Simulation with products, daily stock, and capacity allocation. | New `simulation/engine.py` and `models/schemas.py`. | Implemented |
| "Niche business case" | Transitioned to a general e-commerce/retail use case where supply/demand assumptions are tested. | Scenario builder inputs for Reorder Point, Capacity, and Lead Time. | Implemented |
| "Human-entered values" | Added a Scenario Builder that captures starting stock, replenishment rules, and capacity manually before running. | UI forms in `app/static/index.html` and validation in `app/api/scenarios.py`. | Implemented |
| "Real dataset" | Replaced randomized JSON generation with UCI Online Retail history import capabilities (CSV, XLSX, PDF, Parquet). | `app/imports/` parsers and `data/demo/` dataset. | Implemented |
| "Clear output" | Replaced technical JSON export with a formatted, multi-page business PDF report containing charts and interpretations. | ReportLab implementation in `app/reports/` and PDF download endpoint. | Implemented |
