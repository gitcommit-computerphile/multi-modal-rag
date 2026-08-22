# Multimodal Document RAG





https://github.com/user-attachments/assets/8ffd31c1-9cc1-4a08-810b-6e5836eecd91




A RAG pipeline for PDFs with real tables and charts in them (financial reports mainly). Instead of OCR'ing everything into a soup of text, it detects layout per page, one chunk per region (text/table/figure), and hands tables and charts to a vision model. Page images are kept around too, so at answer time the model can actually look at the chart instead of trusting a text transcription of it.

## How it works

Each page renders to PNG at a fixed DPI, then a layout model (`unstructured` + Tesseract, runs locally on CPU) tags regions as text, table, or figure with bounding boxes. Oversized regions split at natural boundaries rather than a fixed token window. Chunks get embedded and stored in Postgres/pgvector with a pointer back to their source page.

At query time: embed the question, cosine search over chunks, pull in neighboring chunks on the same page for context, load the actual page images for whatever got retrieved, and send text + images to the vision model together.

Conversations persist as sessions with history, so follow-up questions resolve against prior turns instead of starting cold each time.

Vision and embedding providers sit behind a small interface, so it's a config swap rather than a rewrite. Currently OpenAI (`gpt-5.4-mini` + `text-embedding-3-small`), Anthropic wired up as an alternative.

## Running it

```
docker-compose up -d postgres
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
cp .env.example .env   # fill in OPENAI_API_KEY
```

On Windows, layout detection also needs Tesseract and poppler installed natively:

```
winget install UB-Mannheim.TesseractOCR
winget install oschwartz10612.Poppler
```
(open a fresh terminal after so PATH picks it up)

Then:

```
python -m uvicorn api.main:app --reload
python -m streamlit run frontend/streamlit_app.py
```

Upload a PDF in the Streamlit UI, wait for ingestion to finish, ask questions. Chats live in the sidebar, new/delete included.

Other useful scripts:

```
python scripts/ingest_cli.py samples/some_filing.pdf     # ingest without the API
python scripts/debug_layout.py samples/some_filing.pdf   # visualize detected regions
```
