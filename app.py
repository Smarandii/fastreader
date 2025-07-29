"""Main Flask application for FastReader.

This module defines routes and logic to upload PDFs, extract their text,
store metadata in a PostgreSQL database, and serve a web interface that
displays the text using rapid serial visual presentation (RSVP) techniques.

Speed reading research suggests that showing individual words or small
groups of words at a fixed point reduces eye movements (saccades) and
can allow people to read 400 words per minute or more【846068134740725†L17-L23】.  Our
implementation focuses on simplicity rather than scientifically optimized
timing; the user can control the words‑per‑minute (WPM) rate and the
number of words displayed at once.
"""

from __future__ import annotations

import os
import math
from typing import List

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    abort,
)

from sqlalchemy.exc import SQLAlchemyError

from .config import Config, ensure_directories
from .models import Pdf, ReadingLog, init_engine, init_session_factory, init_db

import PyPDF2


def create_app() -> Flask:
    """Application factory pattern used by Flask.

    Returns a configured Flask application.
    """

    app = Flask(__name__)
    app.config.from_object(Config)

    ensure_directories(Config)

    # Initialize database
    engine = init_engine(Config.SQLALCHEMY_DATABASE_URI)
    Session = init_session_factory(engine)
    init_db(engine)

    # Store session factory on app for use in routes
    app.session_factory = Session

    @app.teardown_appcontext
    def remove_session(exception=None):
        # Remove session at the end of the request
        session = getattr(app, "db_session", None)
        if session is not None:
            session.close()
            delattr(app, "db_session")

    def get_session():
        """Get (and lazily create) a SQLAlchemy session bound to the app."""
        session = getattr(app, "db_session", None)
        if session is None:
            session = app.session_factory()
            app.db_session = session
        return session

    def extract_text_from_pdf(file_path: str) -> str:
        """Extract all text from a PDF file using PyPDF2.

        Args:
            file_path: Path to the PDF file.
        Returns:
            A string containing the concatenated text of all pages.
        """
        text_parts: List[str] = []
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                try:
                    page_text = page.extract_text()
                except Exception:
                    page_text = ""
                if page_text:
                    text_parts.append(page_text)
        return "\n".join(text_parts)

    @app.route("/")
    def index():
        """Show the home page with a list of uploaded PDFs and upload form."""
        session = get_session()
        pdfs = session.query(Pdf).order_by(Pdf.uploaded_at.desc()).all()
        return render_template("index.html", pdfs=pdfs)

    @app.route("/upload", methods=["POST"])
    def upload_pdf():
        """Handle PDF upload and text extraction."""
        if "pdf" not in request.files:
            return abort(400, description="No file part in the request")
        file = request.files["pdf"]
        if file.filename == "":
            return abort(400, description="No selected file")
        if not file.filename.lower().endswith(".pdf"):
            return abort(400, description="File must be a PDF")

        filename = file.filename
        upload_dir = app.config["UPLOAD_FOLDER"]
        file_path = os.path.join(upload_dir, filename)
        # Ensure unique filename by adding suffix if needed
        base_name, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(file_path):
            filename = f"{base_name}_{counter}{ext}"
            file_path = os.path.join(upload_dir, filename)
            counter += 1

        file.save(file_path)
        # Extract text
        text = extract_text_from_pdf(file_path)
        # Insert into DB
        session = get_session()
        pdf_record = Pdf(filename=filename, filepath=file_path, content=text)
        session.add(pdf_record)
        session.commit()
        return redirect(url_for("index"))

    @app.route("/reader/<int:pdf_id>")
    def reader(pdf_id: int):
        """Render the reader interface for a given PDF."""
        session = get_session()
        pdf = session.get(Pdf, pdf_id)
        if not pdf:
            return abort(404)
        return render_template("reader.html", pdf=pdf)

    @app.route("/api/text/<int:pdf_id>")
    def get_text(pdf_id: int):
        """Return the text of the PDF split into words.

        The query parameters `chunk` and `separator` are optional; the front‑end
        splits the string into words itself for flexibility. Here we simply
        return the raw text for the PDF so that the client can process it.
        """
        session = get_session()
        pdf = session.get(Pdf, pdf_id)
        if not pdf:
            return abort(404)
        return jsonify({"content": pdf.content})

    @app.route("/api/log/<int:pdf_id>", methods=["POST"])
    def log_session(pdf_id: int):
        """Store a reading session log in the database.

        Expects a JSON payload containing `speed_wpm`, `chunk_size` and optionally
        `duration_seconds`. Returns the created log record ID on success.
        """
        data = request.get_json(force=True, silent=True) or {}
        speed_wpm = int(data.get("speed_wpm", 0))
        chunk_size = int(data.get("chunk_size", 1))
        duration = data.get("duration_seconds")
        if duration is not None:
            try:
                duration = int(duration)
            except (ValueError, TypeError):
                duration = None

        session = get_session()
        pdf = session.get(Pdf, pdf_id)
        if not pdf:
            return abort(404)
        log = ReadingLog(
            pdf_id=pdf_id, speed_wpm=speed_wpm, chunk_size=chunk_size, duration_seconds=duration
        )
        session.add(log)
        session.commit()
        return jsonify({"log_id": log.id})

    return app


if __name__ == "__main__":
    # When running this file directly (e.g. `python app.py`), create the app and run
    # using environment variables for host/port. Defaults to 0.0.0.0:5000 to
    # facilitate access via Docker.
    application = create_app()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    application.run(host=host, port=port, debug=True)