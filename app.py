import sys
from flask import Flask, render_template, request, redirect, url_for, g, jsonify, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
import uuid
import base64

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    internal_dir = os.path.join(BASE_DIR, '_internal')
    template_folder = os.path.join(internal_dir, 'templates') if os.path.exists(os.path.join(internal_dir, 'templates')) else os.path.join(BASE_DIR, 'templates')
    static_folder = os.path.join(internal_dir, 'static') if os.path.exists(os.path.join(internal_dir, 'static')) else os.path.join(BASE_DIR, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'catalogue.db')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Auto-migrate database on start
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create catalogs table
    c.execute("""
    CREATE TABLE IF NOT EXISTS catalogs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    );
    """)
    
    # Seed default catalog
    c.execute("SELECT COUNT(*) FROM catalogs")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO catalogs (id, name) VALUES (1, 'Default Catalog')")
        
    try:
        c.execute("ALTER TABLE products ADD COLUMN group_id TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN group_layout TEXT DEFAULT 'left';")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE products ADD COLUMN image_size INTEGER DEFAULT 0;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE categories ADD COLUMN catalog_id INTEGER DEFAULT 1;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE catalogs ADD COLUMN cover_title TEXT DEFAULT 'PRODUCT CATALOGUE';")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE catalogs ADD COLUMN cover_subtitle TEXT DEFAULT 'Food Packaging Solutions | 2026 Edition';")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE catalogs ADD COLUMN cover_footer TEXT DEFAULT '<strong>Finapack Trading</strong><br>Premium Food Packaging & Industrial Supplies<br>Website: www.finapack.com | Email: info@finapack.com';")
    except sqlite3.OperationalError:
        pass

    try:
        c.execute("UPDATE catalogs SET cover_footer = REPLACE(cover_footer, 'FINAPACK PACKAGING SDN BHD', 'Finapack Trading') WHERE cover_footer LIKE '%FINAPACK PACKAGING SDN BHD%';")
    except Exception:
        pass
        
    conn.commit()
    conn.close()

init_db()

@app.route('/new separate 2.0 catalog finapack/<path:filename>')
def serve_catalog_images(filename):
    catalog_dir = os.path.join(BASE_DIR, 'new separate 2.0 catalog finapack')
    filepath = os.path.join(catalog_dir, filename)
    if not os.path.exists(filepath):
        sanitized = filename.replace(':', '_').replace('"', '_')
        if os.path.exists(os.path.join(catalog_dir, sanitized)):
            filename = sanitized
    return send_from_directory(catalog_dir, filename)

@app.route('/static/uploads/<path:filename>')
def serve_uploads(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# --- API ENDPOINTS FOR WYSIWYG BUILDER ---

@app.route('/api/update_product', methods=['POST'])
def api_update_product():
    data = request.json
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE products SET name=?, price=? WHERE id=?", 
              (data.get('name'), data.get('price'), data.get('prod_id')))
    db.commit()
    return jsonify({"success": True})

@app.route('/api/update_image', methods=['POST'])
def api_update_image():
    prod_id = request.form.get('prod_id')
    image_url = request.form.get('image_url')
    
    db = get_db()
    c = db.cursor()
    
    if 'file' in request.files and request.files['file'].filename != '':
        file = request.files['file']
        filename = secure_filename(str(uuid.uuid4()) + "_" + file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        final_path = 'static/uploads/' + filename
    else:
        final_path = image_url

    if final_path:
        c.execute("SELECT group_id FROM products WHERE id=?", (prod_id,))
        row = c.fetchone()
        group_id = row['group_id'] if row else None
        
        if group_id:
            c.execute("UPDATE products SET image_path=? WHERE group_id=?", (final_path, group_id))
        else:
            c.execute("UPDATE products SET image_path=? WHERE id=?", (final_path, prod_id))
        db.commit()
        
    return jsonify({"success": True, "image_path": final_path})

@app.route('/api/add_product', methods=['POST'])
def api_add_product():
    data = request.json
    db = get_db()
    c = db.cursor()
    
    category_id = data.get('category_id')
    layout = data.get('layout', 'left') # 'left', 'top', or 'right'
    
    # Get max display order in this category
    c.execute("SELECT MAX(display_order) as md FROM products WHERE category_id=?", (category_id,))
    res = c.fetchone()
    order = (res['md'] or 0) + 1
    
    if layout in ('top', 'right'):
        group_id = "group_" + str(uuid.uuid4())
        c.execute("INSERT INTO products (category_id, name, price, image_path, display_order, group_id, group_layout) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (category_id, "NEW BULK ITEM 1", "RM 0.00/UNIT", "new separate 2.0 catalog finapack/bottle/ref_bottle.jpg", order, group_id, layout))
    else:
        c.execute("INSERT INTO products (category_id, name, price, image_path, display_order, group_id, group_layout) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (category_id, "NEW ITEM", "RM 0.00/UNIT", "new separate 2.0 catalog finapack/bottle/ref_bottle.jpg", order, None, 'left'))
        
    db.commit()
    return jsonify({"success": True})

@app.route('/api/add_variation', methods=['POST'])
def api_add_variation():
    data = request.json
    db = get_db()
    c = db.cursor()
    
    prod_id = data.get('prod_id')
    
    c.execute("SELECT category_id, image_path, group_id, group_layout, display_order FROM products WHERE id=?", (prod_id,))
    res = c.fetchone()
    if not res:
        return jsonify({"success": False, "error": "Product not found"}), 404
        
    c.execute("INSERT INTO products (category_id, name, price, image_path, display_order, group_id, group_layout) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (res['category_id'], "NEW VARIATION", "RM 0.00/UNIT", res['image_path'], res['display_order'], res['group_id'], res['group_layout']))
    db.commit()
    return jsonify({"success": True})

@app.route('/api/update_group_layout', methods=['POST'])
def api_update_group_layout():
    data = request.json
    db = get_db()
    c = db.cursor()
    
    prod_id = data.get('prod_id')
    layout = data.get('layout', 'left')
    
    c.execute("SELECT group_id FROM products WHERE id=?", (prod_id,))
    res = c.fetchone()
    group_id = res['group_id'] if res else None
    
    if group_id:
        c.execute("UPDATE products SET group_layout=? WHERE group_id=?", (layout, group_id))
    else:
        c.execute("UPDATE products SET group_layout=? WHERE id=?", (layout, prod_id))
        
    db.commit()
    return jsonify({"success": True})

@app.route('/api/update_image_size', methods=['POST'])
def api_update_image_size():
    data = request.json
    db = get_db()
    c = db.cursor()
    
    prod_id = data.get('prod_id')
    change = data.get('change') # 'up' or 'down'
    
    c.execute("SELECT group_id, group_layout, image_size FROM products WHERE id=?", (prod_id,))
    res = c.fetchone()
    if not res:
        return jsonify({"success": False, "error": "Product not found"}), 404
        
    group_id = res['group_id']
    layout = res['group_layout'] or 'left'
    current_size = res['image_size'] or 0
    
    if current_size == 0:
        if layout == 'top':
            current_size = 150
        elif layout == 'right':
            current_size = 160
        else:
            current_size = 130
            
    step = 30 if layout == 'top' else 20
    if change == 'up':
        new_size = current_size + step
    else:
        new_size = current_size - step
        
    if layout == 'top':
        new_size = max(100, min(new_size, 450))
    elif layout == 'right':
        new_size = max(100, min(new_size, 350))
    else:
        new_size = max(80, min(new_size, 300))
        
    if group_id:
        c.execute("UPDATE products SET image_size=? WHERE group_id=?", (new_size, group_id))
    else:
        c.execute("UPDATE products SET image_size=? WHERE id=?", (new_size, prod_id))
        
    db.commit()
    return jsonify({"success": True})

@app.route('/api/delete_product', methods=['POST'])
def api_delete_product():
    data = request.json
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM products WHERE id=?", (data.get('prod_id'),))
    db.commit()
    return jsonify({"success": True})

@app.route('/api/delete_group', methods=['POST'])
def api_delete_group():
    data = request.json
    db = get_db()
    c = db.cursor()
    
    prod_id = data.get('prod_id')
    c.execute("SELECT group_id FROM products WHERE id=?", (prod_id,))
    res = c.fetchone()
    group_id = res['group_id'] if res else None
    
    if group_id:
        c.execute("DELETE FROM products WHERE group_id=?", (group_id,))
    else:
        c.execute("DELETE FROM products WHERE id=?", (prod_id,))
        
    db.commit()
    return jsonify({"success": True})

@app.route('/api/add_category', methods=['POST'])
def api_add_category():
    data = request.json or {}
    catalog_id = data.get('catalog_id', 1)
    db = get_db()
    c = db.cursor()
    c.execute("SELECT MAX(display_order) as md FROM categories WHERE catalog_id = ?", (catalog_id,))
    res = c.fetchone()
    order = (res['md'] or 0) + 1
    c.execute("INSERT INTO categories (name, display_order, catalog_id) VALUES (?, ?, ?)", ("NEW CATEGORY", order, catalog_id))
    db.commit()
    return jsonify({"success": True})

@app.route('/api/delete_category', methods=['POST'])
def api_delete_category():
    data = request.json
    db = get_db()
    c = db.cursor()
    c.execute("DELETE FROM products WHERE category_id=?", (data.get('category_id'),))
    c.execute("DELETE FROM categories WHERE id=?", (data.get('category_id'),))
    db.commit()
    return jsonify({"success": True})

@app.route('/api/update_category_name', methods=['POST'])
def api_update_category_name():
    data = request.json
    db = get_db()
    c = db.cursor()
    c.execute("UPDATE categories SET name=? WHERE id=?", (data.get('name'), data.get('category_id')))
    db.commit()
    return jsonify({"success": True})

# --- CATALOG MANAGEMENT & BACKUP ENDPOINTS ---

@app.route('/api/create_catalog', methods=['POST'])
def api_create_catalog():
    data = request.json or {}
    name = data.get('name', 'New Catalog').strip()
    if not name:
        return jsonify({"success": False, "error": "Catalog name cannot be empty"}), 400
        
    db = get_db()
    c = db.cursor()
    try:
        c.execute("INSERT INTO catalogs (name) VALUES (?)", (name,))
        db.commit()
        catalog_id = c.lastrowid
        return jsonify({"success": True, "catalog_id": catalog_id})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "A catalog with this name already exists."}), 400

@app.route('/api/rename_catalog', methods=['POST'])
def api_rename_catalog():
    data = request.json or {}
    catalog_id = data.get('catalog_id')
    new_name = data.get('name', '').strip()
    if not new_name:
        return jsonify({"success": False, "error": "Catalog name cannot be empty"}), 400
        
    db = get_db()
    c = db.cursor()
    try:
        c.execute("UPDATE catalogs SET name=? WHERE id=?", (new_name, catalog_id))
        db.commit()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "A catalog with this name already exists."}), 400

@app.route('/api/delete_catalog', methods=['POST'])
def api_delete_catalog():
    data = request.json or {}
    catalog_id = data.get('catalog_id')
    
    if catalog_id == 1:
        return jsonify({"success": False, "error": "Cannot delete the default catalog."}), 400
        
    db = get_db()
    c = db.cursor()
    
    # 1. Delete all products belonging to categories in this catalog
    c.execute("SELECT id FROM categories WHERE catalog_id=?", (catalog_id,))
    cat_ids = [r['id'] for r in c.fetchall()]
    if cat_ids:
        placeholders = ','.join('?' for _ in cat_ids)
        c.execute(f"DELETE FROM products WHERE category_id IN ({placeholders})", cat_ids)
        
    # 2. Delete categories
    c.execute("DELETE FROM categories WHERE catalog_id=?", (catalog_id,))
    
    # 3. Delete catalog entry
    c.execute("DELETE FROM catalogs WHERE id=?", (catalog_id,))
    
    db.commit()
    return jsonify({"success": True})

import base64

@app.route('/api/export_catalog')
def api_export_catalog():
    catalog_id = request.args.get('catalog_id', 1, type=int)
    db = get_db()
    c = db.cursor()
    
    # Get catalog name
    c.execute("SELECT name FROM catalogs WHERE id=?", (catalog_id,))
    cat_row = c.fetchone()
    catalog_name = cat_row['name'] if cat_row else "Catalog"
    
    # Get categories
    c.execute("SELECT id, name, display_order FROM categories WHERE catalog_id=? ORDER BY display_order", (catalog_id,))
    categories = [dict(row) for row in c.fetchall()]
    
    # Get products for all categories in this catalog
    cat_ids = [cat['id'] for cat in categories]
    products = []
    if cat_ids:
        placeholders = ','.join('?' for _ in cat_ids)
        c.execute(f"SELECT * FROM products WHERE category_id IN ({placeholders}) ORDER BY display_order, id", cat_ids)
        products = [dict(row) for row in c.fetchall()]
        
    # Serialize images as base64
    for prod in products:
        img_path = prod['image_path']
        if img_path and os.path.exists(img_path) and os.path.isfile(img_path):
            try:
                with open(img_path, 'rb') as f:
                    img_data = f.read()
                ext = img_path.split('.')[-1].lower()
                mime = 'image/jpeg' if ext in ('jpg', 'jpeg') else ('image/png' if ext == 'png' else 'image/webp')
                b64_str = base64.b64encode(img_data).decode('utf-8')
                prod['image_base64'] = f"data:{mime};base64,{b64_str}"
            except Exception as e:
                print(f"Error base64 encoding {img_path}: {e}")
                prod['image_base64'] = None
        else:
            prod['image_base64'] = None

    backup_data = {
        'catalog_name': catalog_name,
        'categories': categories,
        'products': products
    }
    
    # Clean filename
    safe_name = "".join(x for x in catalog_name if x.isalnum() or x in (" ", "_", "-")).strip().replace(" ", "_")
    
    response = jsonify(backup_data)
    response.headers.set('Content-Disposition', f'attachment; filename=backup_{safe_name}.json')
    return response

@app.route('/api/import_catalog', methods=['POST'])
def api_import_catalog():
    catalog_id = request.form.get('catalog_id', type=int)
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Empty filename"}), 400
        
    import json
    try:
        backup_data = json.load(file)
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid JSON file: {e}"}), 400
        
    categories = backup_data.get('categories', [])
    products = backup_data.get('products', [])
    
    db = get_db()
    c = db.cursor()
    
    # 1. Delete existing categories and products in this catalog
    c.execute("SELECT id FROM categories WHERE catalog_id=?", (catalog_id,))
    old_cat_ids = [r['id'] for r in c.fetchall()]
    if old_cat_ids:
        placeholders = ','.join('?' for _ in old_cat_ids)
        c.execute(f"DELETE FROM products WHERE category_id IN ({placeholders})", old_cat_ids)
    c.execute("DELETE FROM categories WHERE catalog_id=?", (catalog_id,))
    
    # 2. Insert categories and map old category IDs to new category IDs
    cat_id_map = {}
    for cat in categories:
        old_id = cat['id']
        c.execute("INSERT INTO categories (name, display_order, catalog_id) VALUES (?, ?, ?)",
                  (cat['name'], cat['display_order'], catalog_id))
        new_id = c.lastrowid
        cat_id_map[old_id] = new_id
        
    # 3. Insert products, decoding Base64 images if present
    for prod in products:
        old_cat_id = prod['category_id']
        new_cat_id = cat_id_map.get(old_cat_id)
        if not new_cat_id:
            continue
            
        image_path = prod['image_path']
        b64_str = prod.get('image_base64')
        
        if b64_str and b64_str.startswith('data:image/'):
            try:
                header, data_part = b64_str.split(';base64,')
                ext = header.split('/')[-1]
                if ext == 'jpeg': ext = 'jpg'
                
                filename = f"{uuid.uuid4()}_backup.{ext}"
                target_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                with open(target_path, 'wb') as f:
                    f.write(base64.b64decode(data_part))
                image_path = f"static/uploads/{filename}"
            except Exception as e:
                print(f"Error decoding base64 image: {e}")
                
        c.execute("""
            INSERT INTO products (category_id, name, price, image_path, display_order, group_id, group_layout, image_size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_cat_id,
            prod['name'],
            prod['price'],
            image_path,
            prod['display_order'],
            prod.get('group_id'),
            prod.get('group_layout') or 'left',
            prod.get('image_size') or 0
        ))
        
    db.commit()
    return jsonify({"success": True})

# --- MAIN BUILDER VIEW ---

@app.route('/')
def builder_view():
    mode = request.args.get('mode', 'list')
    db = get_db()
    c = db.cursor()
    
    # Get active catalog_id
    c.execute("SELECT id, name FROM catalogs ORDER BY id")
    catalogs_rows = c.fetchall()
    all_catalogs = [dict(r) for r in catalogs_rows]
    
    catalog_id = request.args.get('catalog_id', type=int)
    if not catalog_id or not any(cat['id'] == catalog_id for cat in all_catalogs):
        catalog_id = all_catalogs[0]['id'] if all_catalogs else 1
        
    c.execute("SELECT name, cover_title, cover_subtitle, cover_footer FROM catalogs WHERE id=?", (catalog_id,))
    cat_row = c.fetchone()
    active_catalog_name = cat_row['name'] if cat_row else "Catalog"
    cover_title = cat_row['cover_title'] if cat_row and cat_row['cover_title'] else "PRODUCT CATALOGUE"
    cover_subtitle = cat_row['cover_subtitle'] if cat_row and cat_row['cover_subtitle'] else "Food Packaging Solutions | 2026 Edition"
    cover_footer = cat_row['cover_footer'] if cat_row and cat_row['cover_footer'] else "<strong>Finapack Trading</strong><br>Premium Food Packaging & Industrial Supplies<br>Website: www.finapack.com | Email: info@finapack.com"
    
    c.execute("SELECT * FROM categories WHERE catalog_id = ? ORDER BY display_order", (catalog_id,))
    categories = c.fetchall()
    
    ordered_cats = []
    for cat in categories:
        c.execute("SELECT * FROM products WHERE category_id = ? ORDER BY display_order, id", (cat['id'],))
        prods = c.fetchall()
        
        # Group products into blocks by group_id
        blocks_map = {}
        blocks_list = []
        for p in prods:
            p_dict = dict(p)
            gid = p_dict.get('group_id')
            if gid:
                if gid not in blocks_map:
                    block = {
                        'group_id': gid,
                        'image_path': p_dict['image_path'],
                        'group_layout': p_dict.get('group_layout') or 'left',
                        'image_size': p_dict.get('image_size') or 0,
                        'elements': []
                    }
                    blocks_map[gid] = block
                    blocks_list.append(block)
                blocks_map[gid]['elements'].append(p_dict)
            else:
                block = {
                    'group_id': None,
                    'image_path': p_dict['image_path'],
                    'group_layout': p_dict.get('group_layout') or 'left',
                    'image_size': p_dict.get('image_size') or 0,
                    'elements': [p_dict]
                }
                blocks_list.append(block)
                
        ordered_cats.append({'id': cat['id'], 'name': cat['name'], 'products': prods, 'blocks': blocks_list})
            
    MAX_PAGE_HEIGHT = 760
    HEADER_HEIGHT = 45 

    new_pages = []
    current_page_items = []
    current_height = 0

    for cat in ordered_cats:
        cat_name = cat['name']
        cat_id = cat['id']
        blocks = cat['blocks']
        
        def calc_block_h(block):
            layout = block.get('group_layout') or 'left'
            size = block.get('image_size') or 0
            if layout == 'top':
                h = size if size > 0 else 150
                return h + sum([len(i['price'].split('\n')) * 15 + 30 for i in block['elements']]) + 10
            else:
                if mode == 'list' or block.get('group_id'):
                    BASE_BLOCK_HEIGHT = size if size > 0 else 130
                    return max(BASE_BLOCK_HEIGHT, sum([len(i['price'].split('\n')) * 15 + 30 for i in block['elements']])) + 8
                else:
                    img_h = size if size > 0 else 120
                    BASE_BLOCK_HEIGHT = img_h + 100
                    return max(BASE_BLOCK_HEIGHT, sum([len(i['price'].split('\n')) * 15 + img_h + 10 for i in block['elements']])) + 15
                
        visual_rows = []
        if not blocks:
            visual_rows.append({'type': 'empty'})
        else:
            if mode == 'list':
                for b in blocks:
                    visual_rows.append({'type': 'row', 'row_blocks': [b]})
            else:
                current_group = []
                for b in blocks:
                    if b.get('group_id'):
                        if current_group:
                            visual_rows.append({'type': 'row', 'row_blocks': current_group})
                            current_group = []
                        visual_rows.append({'type': 'row', 'row_blocks': [b]})
                    else:
                        current_group.append(b)
                        if len(current_group) == 3:
                            visual_rows.append({'type': 'row', 'row_blocks': current_group})
                            current_group = []
                if current_group:
                    visual_rows.append({'type': 'row', 'row_blocks': current_group})

        first_row_h = 0
        if visual_rows and visual_rows[0]['type'] == 'row':
            first_row_h = max([calc_block_h(b) for b in visual_rows[0]['row_blocks']])
        elif visual_rows and visual_rows[0]['type'] == 'empty':
            first_row_h = 80
            
        needed_for_start = HEADER_HEIGHT + first_row_h
        
        if current_height + needed_for_start > MAX_PAGE_HEIGHT:
            if current_page_items:
                new_pages.append(current_page_items)
                current_page_items = []
                current_height = 0
                
        current_page_items.append({'type': 'header', 'text': cat_name, 'cat_id': cat_id})
        current_height += HEADER_HEIGHT
        
        for idx, v_row in enumerate(visual_rows):
            if v_row['type'] == 'empty':
                row_h = 80
            else:
                row_h = max([calc_block_h(b) for b in v_row['row_blocks']])
                
            if current_height + row_h > MAX_PAGE_HEIGHT:
                new_pages.append(current_page_items)
                current_page_items = []
                current_height = 0
                current_page_items.append({'type': 'header', 'text': cat_name, 'cat_id': cat_id, 'is_cont': True})
                current_height += HEADER_HEIGHT
                
            is_last = (idx == len(visual_rows) - 1)
            current_page_items.append({'type': 'chunk', 'mode': mode, 'row': v_row, 'cat_id': cat_id, 'is_last': is_last})
            current_height += row_h

    if current_page_items:
        new_pages.append(current_page_items)

    return render_template(
        'builder.html',
        pages=new_pages,
        mode=mode,
        categories=ordered_cats,
        catalogs=all_catalogs,
        active_catalog_id=catalog_id,
        active_catalog_name=active_catalog_name,
        cover_title=cover_title,
        cover_subtitle=cover_subtitle,
        cover_footer=cover_footer
    )

@app.route('/api/update_cover', methods=['POST'])
def api_update_cover():
    data = request.json
    catalog_id = data.get('catalog_id', 1)
    field = data.get('field')
    value = data.get('value', '')
    
    db = get_db()
    c = db.cursor()
    
    if field == 'title':
        c.execute("UPDATE catalogs SET cover_title = ? WHERE id = ?", (value, catalog_id))
    elif field == 'subtitle':
        c.execute("UPDATE catalogs SET cover_subtitle = ? WHERE id = ?", (value, catalog_id))
    elif field == 'footer':
        c.execute("UPDATE catalogs SET cover_footer = ? WHERE id = ?", (value, catalog_id))
        
    db.commit()
    return jsonify({"success": True})

@app.route('/api/swap_products', methods=['POST'])
def api_swap_products():
    data = request.json
    prod1 = data.get('prod1_id')
    prod2 = data.get('prod2_id')
    db = get_db()
    c = db.cursor()
    
    c.execute("SELECT id, display_order, group_id FROM products WHERE id=?", (prod1,))
    p1 = c.fetchone()
    c.execute("SELECT id, display_order, group_id FROM products WHERE id=?", (prod2,))
    p2 = c.fetchone()
    
    if p1 and p2:
        o1 = p1['display_order']
        o2 = p2['display_order']
        
        g1 = p1['group_id']
        g2 = p2['group_id']
        
        if g1:
            c.execute("UPDATE products SET display_order=? WHERE group_id=?", (o2, g1))
        else:
            c.execute("UPDATE products SET display_order=? WHERE id=?", (o2, p1['id']))
            
        if g2:
            c.execute("UPDATE products SET display_order=? WHERE group_id=?", (o1, g2))
        else:
            c.execute("UPDATE products SET display_order=? WHERE id=?", (o1, p2['id']))
            
        db.commit()
    return jsonify(success=True)

@app.route('/api/reorder_categories', methods=['POST'])
def api_reorder_categories():
    data = request.json
    cat_ids = data.get('category_ids', [])
    db = get_db()
    c = db.cursor()
    for idx, cid in enumerate(cat_ids):
        c.execute("UPDATE categories SET display_order=? WHERE id=?", (idx, cid))
    db.commit()
    return jsonify(success=True)

@app.route('/api/sort_categories_az', methods=['POST'])
def api_sort_categories_az():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT id FROM categories ORDER BY name ASC")
    cats = c.fetchall()
    for idx, row in enumerate(cats):
        c.execute("UPDATE categories SET display_order=? WHERE id=?", (idx, row['id']))
    db.commit()
    return jsonify(success=True)

@app.route('/api/delete_multiple', methods=['POST'])
def api_delete_multiple():
    data = request.json
    db = get_db()
    c = db.cursor()
    for pid in data.get('prod_ids', []):
        c.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit()
    return jsonify(success=True)

@app.route('/api/move_multiple_products', methods=['POST'])
def api_move_multiple_products():
    data = request.json or {}
    prod_ids = data.get('prod_ids', [])
    category_id = data.get('category_id')
    new_category_name = data.get('new_category_name', '').strip()
    catalog_id = data.get('catalog_id', 1)
    
    if not prod_ids:
        return jsonify({"success": False, "error": "No products selected."}), 400
        
    db = get_db()
    c = db.cursor()
    
    if new_category_name:
        c.execute("SELECT MAX(display_order) as md FROM categories WHERE catalog_id = ?", (catalog_id,))
        res = c.fetchone()
        order = (res['md'] or 0) + 1
        c.execute("INSERT INTO categories (name, display_order, catalog_id) VALUES (?, ?, ?)",
                  (new_category_name, order, catalog_id))
        category_id = c.lastrowid
        
    if not category_id:
        return jsonify({"success": False, "error": "Target category is invalid."}), 400
        
    c.execute("SELECT MAX(display_order) as md FROM products WHERE category_id = ?", (category_id,))
    res = c.fetchone()
    start_order = (res['md'] or 0) + 1
    
    for idx, pid in enumerate(prod_ids):
        c.execute("SELECT group_id FROM products WHERE id=?", (pid,))
        p_row = c.fetchone()
        group_id = p_row['group_id'] if p_row else None
        
        if group_id:
            c.execute("UPDATE products SET category_id=?, display_order=? WHERE group_id=?", 
                      (category_id, start_order + idx, group_id))
        else:
            c.execute("UPDATE products SET category_id=?, display_order=? WHERE id=?", 
                      (category_id, start_order + idx, pid))
            
    db.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(port=5001, debug=True)
