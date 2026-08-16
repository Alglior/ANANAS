import gzip
import re
import tempfile

from flask import current_app, jsonify, redirect, request, send_file, url_for
from sqlalchemy import inspect, text, MetaData, Table
from sqlalchemy.schema import CreateTable
from app import db

from src.admin import bp, login_required, require_admin, api_admin_required

MAX_RESTORE_SIZE = 100 * 1024 * 1024  # 100 Mo

_RESTORE_ALLOWED = [
    (
        re.compile(r"^CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)\s*\(", re.I),
        None,
    ),
    (
        re.compile(r"^CREATE\s+OR\s+REPLACE\s+VIEW\s+(\w+)\s+AS\s+", re.I),
        None,
    ),
    (
        re.compile(r"^INSERT\s+INTO\s+(\w+)\s*\([^)]*\)\s*VALUES", re.I),
        lambda c: not _has_select_outside_strings(c),
    ),
    (
        re.compile(r"^DELETE\s+FROM\s+(\w+)", re.I),
        lambda c: not _has_select_outside_strings(c),
    ),
    (
        re.compile(r"^SELECT\s+setval\s*\(", re.I),
        None,
    ),
]


def _has_select_outside_strings(stmt):
    in_string = False
    i = 0
    while i < len(stmt):
        ch = stmt[i]
        if in_string:
            if ch == "'":
                if i + 1 < len(stmt) and stmt[i + 1] == "'":
                    i += 2
                    continue
                in_string = False
            i += 1
            continue
        if ch == "'":
            in_string = True
            i += 1
            continue
        if stmt[i:].upper().startswith("SELECT") and (
            i + 6 >= len(stmt) or not stmt[i + 6].isalpha()
        ):
            return True
        i += 1
    return False


def _is_allowed_restore_statement(stmt, valid_tables):
    compact = " ".join(stmt.split())
    for pattern, validator in _RESTORE_ALLOWED:
        m = pattern.match(compact)
        if m:
            if validator and not validator(compact):
                return False
            # Restreint les tables cibles à celles existant déjà dans le schéma,
            # pour empêcher la création/drop de tables arbitraires via le fichier.
            if m.lastindex and m.group(1):
                table = m.group(1).lower()
                if valid_tables and table not in valid_tables:
                    return False
            return True
    return False


@bp.route("/admin/backup")
@login_required
@require_admin
def admin_backup_page():
    return redirect(url_for("admin.admin_settings"))


@bp.route("/api/admin/backup/download")
@login_required
@api_admin_required
def admin_backup_download():

    engine = db.engine
    dialect = engine.dialect.name
    is_pg = dialect == "postgresql"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sql.gz")
    try:
        with gzip.open(tmp.name, "wt", encoding="utf-8") as gz:
            _write_header(gz)

            inspector = inspect(engine)
            table_names = inspector.get_table_names()

            for table_name in table_names:
                _dump_table(gz, engine, table_name, is_pg)

            if is_pg:
                _fix_sequences(gz, engine, table_names)

        return send_file(
            tmp.name,
            mimetype="application/gzip",
            as_attachment=True,
            download_name=(
                f"ananas_backup_"
                f"{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}"
                f".sql.gz"
            ),
        )
    except Exception as e:
        current_app.logger.error("Backup failed: %s", str(e))
        return jsonify({"error": f"Erreur lors de la sauvegarde : {str(e)}"}), 500
    finally:
        import os
        os.unlink(tmp.name)


@bp.route("/api/admin/backup/restore", methods=["POST"])
@login_required
@api_admin_required
def admin_backup_restore():

    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400

    f = request.files["file"]
    if not f.filename or not f.filename.endswith(".sql.gz"):
        return jsonify({"error": "Le fichier doit être au format .sql.gz"}), 400

    raw = f.read()
    if not raw:
        return jsonify({"error": "Fichier vide"}), 400
    if len(raw) > MAX_RESTORE_SIZE:
        return jsonify({"error": "Fichier trop volumineux"}), 400

    try:
        decompressed = gzip.decompress(raw).decode("utf-8")
    except Exception:
        return jsonify({"error": "Impossible de décompresser le fichier"}), 400

    engine = db.engine
    valid_tables = {t.lower() for t in inspect(engine).get_table_names()}

    sql_statements = []
    current_stmt = []
    for line in decompressed.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            if current_stmt:
                current_stmt.append("")
            continue
        current_stmt.append(line)
        if stripped.endswith(";"):
            sql_statements.append("\n".join(current_stmt))
            current_stmt = []
    if current_stmt:
        sql_statements.append("\n".join(current_stmt))

    table_names = []
    for stmt in sql_statements:
        stmt_clean = stmt.strip().upper()
        if stmt_clean.startswith("CREATE TABLE"):
            m = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", stmt_clean)
            if m:
                table_names.append(m.group(1))

    executed = 0
    errors = []

    try:
        with engine.connect() as conn:
            conn.execution_options(isolation_level="AUTOCOMMIT")
            conn.execute(text("SET session_replication_role = 'replica'"))
            executed += 1
            for stmt in sql_statements:
                stmt = stmt.strip()
                if not stmt:
                    continue
                stmt_upper = stmt.upper().strip()
                if stmt_upper.startswith("SET "):
                    continue
                if not _is_allowed_restore_statement(stmt, valid_tables):
                    errors.append({
                        "statement": stmt[:200],
                        "error": "Instruction non autorisée",
                    })
                    return jsonify({
                        "error": "Restauration annulée : instruction non autorisée détectée",
                        "errors": errors,
                        "executed": executed,
                    }), 400
                try:
                    conn.execute(text(stmt))
                    executed += 1
                except Exception as e:
                    err_str = str(e)
                    if "already exists" in err_str or "duplicate" in err_str.lower():
                        continue
                    errors.append({"statement": stmt[:200], "error": err_str})
                    if len(errors) >= 10:
                        errors.append({"error": "Trop d'erreurs, restauration annulée"})
                        return jsonify({
                            "error": "Restauration annulée après plusieurs erreurs",
                            "errors": errors,
                            "executed": executed,
                        }), 500

            try:
                conn.execute(text("SET session_replication_role = 'origin'"))
            except Exception:
                pass
    except Exception as e:
        return jsonify({"error": f"Erreur de connexion : {str(e)}"}), 500

    return jsonify({
        "message": f"Restauration terminée : {executed} instructions exécutées",
        "executed": executed,
        "errors": errors,
    })


def _write_header(gz):
    gz.write("-- ANANAS database backup\n")
    gz.write(f"-- Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")
    gz.write("SET statement_timeout = 0;\n")
    gz.write("SET lock_timeout = 0;\n")
    gz.write("SET client_encoding = 'UTF8';\n")
    gz.write("SET standard_conforming_strings = on;\n\n")


def _quote(val):
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, bytes):
        return f"'\\x{val.hex()}'"
    if isinstance(val, (dict, list)):
        import json
        escaped = json.dumps(val, ensure_ascii=False).replace("'", "''")
        return f"'{escaped}'"
    escaped = str(val).replace("'", "''").replace("\\", "\\\\")
    return f"'{escaped}'"


def _dump_table(gz, engine, table_name, is_pg):
    inspector = inspect(engine)
    columns = inspector.get_columns(table_name)
    col_names = [c["name"] for c in columns]
    col_list = ", ".join(col_names)

    gz.write(f"--\n-- Table: {table_name}\n--\n")

    with engine.connect() as conn:
        if is_pg:
            rel = conn.execute(
                text("SELECT relkind FROM pg_catalog.pg_class WHERE relname = :t"),
                {"t": table_name},
            ).scalar()
            if rel == "v":
                view_def = conn.execute(
                    text("SELECT pg_catalog.pg_get_viewdef(c.oid, true) FROM pg_catalog.pg_class c WHERE c.relname = :t"),
                    {"t": table_name},
                ).scalar()
                if view_def:
                    gz.write(f"CREATE OR REPLACE VIEW {table_name} AS {view_def};\n\n")
                return

        meta = MetaData()
        table = Table(table_name, meta, autoload_with=engine)
        create_sql = str(CreateTable(table).compile(engine))
        gz.write(create_sql + ";\n\n")

        rows = conn.execute(text(f"SELECT * FROM {table_name}")).fetchall()

    if not rows:
        gz.write(f"DELETE FROM {table_name};\n\n")
        return

    gz.write(f"DELETE FROM {table_name};\n\n")
    gz.write(f"INSERT INTO {table_name} ({col_list}) VALUES\n")

    vals_lines = []
    for row in rows:
        vals = [_quote(row[i]) for i in range(len(col_names))]
        vals_lines.append(f"({', '.join(vals)})")

    gz.write(",\n".join(vals_lines))
    gz.write(";\n\n")


def _fix_sequences(gz, engine, table_names):
    gz.write("--\n-- Reset sequences\n--\n")
    with engine.connect() as conn:
        for table_name in table_names:
            inspector = inspect(engine)
            pk_info = inspector.get_pk_constraint(table_name)
            pk_cols = pk_info.get("constrained_columns", []) if pk_info else []
            if not pk_cols:
                continue
            for col in pk_cols:
                seq_name = conn.execute(
                    text("SELECT pg_catalog.pg_get_serial_sequence(:t, :c)"),
                    {"t": table_name, "c": col},
                ).scalar()
                if seq_name:
                    max_id = conn.execute(
                        text(f"SELECT COALESCE(MAX({col}), 0) FROM {table_name}")
                    ).scalar() or 0
                    gz.write(f"SELECT setval('{seq_name}', {max_id + 1}, false);\n")
        conn.close()