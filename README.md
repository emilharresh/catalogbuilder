# Finapack Catalog Builder

An interactive, desktop-enabled **WYSIWYG Product Catalog Builder** built with Python Flask, Waitress WSGI, SQLite, and an A4 pixel-accurate print engine. It allows packaging and wholesale businesses to visually compose, edit, paginate, and export multi-page product catalogues directly into print-ready A4 PDFs or standalone portable Windows applications.

---

## 🌟 Key Features

1. **WYSIWYG Visual Editor**:
   - In-place text editing for product titles, prices, descriptions, and category names.
   - Drag-and-drop or one-click swapping of product card positions and categories.
   - Built-in **Cropper.js** integration to crop, rotate, and aspect-fit product images.

2. **Automated Server-Side A4 Pagination**:
   - Dynamically calculates pixel-height budgets (`MAX_PAGE_HEIGHT = 760px`) considering individual image sizes and line heights.
   - Automatically handles category overflow by generating seamless continuation headers across pages.

3. **Multiple Variant Layouts**:
   - **Left Layout**: Standard side-by-side thumbnail with variant specifications list.
   - **Top Layout**: Banner image card with pricing tables below.
   - **Right Layout**: Right-aligned imagery with left-aligned specs.
   - Dynamic per-block image scaling adjustments.

4. **Multi-Catalog & Backup System**:
   - Create and switch between multiple catalogs (e.g., Seasonal, Core, Distributor).
   - One-click **JSON Export/Import** with all product photos automatically converted to Base64 strings for 100% portable backups.

5. **A4 Print & PDF Generation**:
   - Native browser print stylesheet (`@media print`) calibrated strictly for `size: A4 portrait; margin: 0;`.
   - Generates interactive Table of Contents (TOC) and front cover page with custom branding.

6. **Portable Desktop Distribution**:
   - Runs locally without requiring terminal knowledge or prior Python installation when packaged via PyInstaller.
   - Automatically finds a free port and launches the user's default browser.

---

## 📂 Project Architecture & Directory Layout

```text
catalog_clean/
├── app.py                     # Core Flask backend, SQLite models & REST API
├── run_desktop.py             # Desktop launcher (Waitress WSGI + auto-browser)
├── FinapackCatalogBuilder.spec# PyInstaller packaging recipe for Windows EXE
├── catalogue.db               # SQLite database (catalogs, categories, products)
├── requirements.txt           # Python dependency specifications
├── .gitignore                 # Files excluded from version control
├── README.md                  # Project documentation
│
├── templates/                 # Jinja2 HTML View Templates
│   ├── builder.html           # Main WYSIWYG visual builder UI
│   ├── admin.html             # Table-based inventory manager
│   └── print.html             # Minimalist live PDF print preview
│
├── static/                    # Static web assets
│   ├── finapacklogo.png       # Company branding logo
│   └── uploads/               # User-uploaded product imagery
│
└── new separate 2.0 catalog finapack/ # Source image library for catalog items
```

---

## 🛠️ How It Works (Methods & Architecture)

### 1. Dynamic Height Pagination Engine (`app.py`)
To prevent products from cutting off awkwardly across printed pages, `app.py` implements a height-budgeting algorithm:
- Every block layout (single item or variant group) is evaluated:
  $$\text{Height} = \text{Image Height} + \sum(\text{Price Lines} \times 15\text{px} + 30\text{px}) + \text{Padding}$$
- When a page approaches `MAX_PAGE_HEIGHT` (760px), a new page is started, and a continuation category banner (`is_cont: True`) is inserted automatically.

### 2. Dual Desktop / Web Deployment Model
- In development, the app runs via Flask's local server.
- In desktop mode, `run_desktop.py` binds Waitress WSGI to `127.0.0.1` on a dynamically checked port (avoiding `Port in use` conflicts), then launches the user's default browser on a background thread.
- PyInstaller bundles Waitress, Flask, and the Jinja2 templates into `dist/FinapackCatalogBuilder/FinapackCatalogBuilder.exe`.

### 3. Base64 Portable Catalog Serialization
- The export endpoint (`/api/export_catalog`) reads binary image files from disk and embeds them as `data:image/...;base64,...` strings inside a JSON payload.
- On import (`/api/import_catalog`), the JSON is parsed, Base64 strings are saved into `static/uploads/`, and database records are re-indexed.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+ (Python 3.11 – 3.13 tested)

### Installation
1. Clone or extract the repository:
   ```bash
   git clone <your-repository-url>
   cd catalog_clean
   ```

2. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # Windows (Command Prompt):
   .venv\Scripts\activate.bat
   # Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application
- **Standard Desktop Runner (Recommended)**:
  ```bash
  python run_desktop.py
  ```
  *Your browser will automatically open to `http://127.0.0.1:5001`.*

- **Development Mode with Hot-Reload**:
  ```bash
  python app.py
  ```

---

## 📦 Packaging Standalone Windows `.exe`
To compile a standalone portable folder containing `FinapackCatalogBuilder.exe`:
```bash
pyinstaller --clean FinapackCatalogBuilder.spec
```
The output will be generated inside the `dist/FinapackCatalogBuilder/` folder.

---

## 📄 License
Internal proprietary catalog management software for Finapack Trading.
