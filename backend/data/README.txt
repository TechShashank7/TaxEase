Place the Income Tax Act PDF in this directory before running ingestion.

Expected filename: income_tax_act.pdf

Source: Income Tax Department of India
URL:    https://incometaxindia.gov.in/pages/acts/income-tax-act.aspx

The ingestion pipeline reads this file, extracts text, chunks it by section,
and stores chunks with full metadata ready for embedding and Qdrant indexing.

Sprint 1 output: backend/data/ingestion_log.json (auto-generated after run)
