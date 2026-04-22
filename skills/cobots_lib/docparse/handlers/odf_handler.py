"""
odf_handler.py - OpenDocument Format handler.

Supports ``.odt``, ``.ods``, and ``.odp`` via ``odfpy`` with a
LibreOffice headless fallback.
"""

from __future__ import annotations

import logging
import os
import shutil

from cobots_lib.docparse.constants import (
    LIBREOFFICE_TIMEOUT,
    MAX_OUTPUT_SIZE,
)
from cobots_lib.docparse.errors import (
    DependencyMissingError,
    ParseError,
)
from cobots_lib.docparse.handlers.base import BaseHandler
from cobots_lib.docparse.result import ParseResult
from cobots_lib.docparse.security import (
    run_libreoffice_with_lock,
    secure_temp_dir,
    validate_archive,
    validate_odf_xml,
    write_lo_profile_security,
)

_log = logging.getLogger(__name__)


class OdfHandler(BaseHandler):
    """Handler for ODF files (``.odt``, ``.ods``, ``.odp``).

    Uses ``odfpy`` as the primary engine with a LibreOffice headless
    fallback.
    """

    @property
    def extensions(self) -> list[str]:
        return [".odt", ".ods", ".odp"]

    @property
    def name(self) -> str:
        return "ODF"

    def available(self) -> bool:
        return self._has_odfpy() or self._has_libreoffice()

    def parse(self, file_path: str, **kwargs) -> ParseResult:
        ext = os.path.splitext(file_path)[1].lower()

        # Validate archive first.
        validate_archive(file_path)

        # Pre-validate XML content with defusedxml to protect
        # against billion-laughs / XML bomb attacks in odfpy's
        # internal SAX parser.
        validate_odf_xml(file_path)

        if self._has_odfpy():
            return self._parse_with_odfpy(file_path, ext, **kwargs)

        if self._has_libreoffice():
            return self._parse_with_libreoffice(
                file_path, ext, **kwargs
            )

        raise DependencyMissingError(
            "ODF conversion requires odfpy (pip install odfpy) "
            "or LibreOffice (apt install libreoffice)."
        )

    # ----------------------------------------------------------------
    # odfpy path
    # ----------------------------------------------------------------

    def _parse_with_odfpy(
        self, file_path: str, ext: str, **kwargs
    ) -> ParseResult:
        """Parse an ODF file using ``odfpy``."""
        try:
            from odf.opendocument import load as odf_load
            from odf import text as odf_text
            from odf import table as odf_table
        except ImportError:
            raise ParseError(
                "odfpy import failed despite availability check."
            )

        try:
            doc = odf_load(file_path)
        except Exception as exc:
            raise ParseError(
                "Failed to load ODF document.",
                detail=f"{type(exc).__name__}: {exc}",
            ) from exc

        if ext == ".odt":
            content = self._extract_odt(doc, odf_text)
        elif ext == ".ods":
            content = self._extract_ods(doc, odf_table)
        elif ext == ".odp":
            content = self._extract_odp(doc, odf_text)
        else:
            content = self._extract_odt(doc, odf_text)

        if len(content) > MAX_OUTPUT_SIZE:
            content = content[:MAX_OUTPUT_SIZE]

        return ParseResult(
            content=content,
            output_format="markdown",
            source_path=file_path,
            source_format=ext,
            handler_name=self.name,
            metadata={"word_count": len(content.split())},
        )

    @staticmethod
    def _get_text(node) -> str:
        """Recursively extract text from an ODF XML node."""
        result: list[str] = []
        if hasattr(node, "childNodes"):
            for child in node.childNodes:
                if hasattr(child, "data"):
                    result.append(child.data)
                else:
                    result.append(OdfHandler._get_text(child))
        return "".join(result)

    def _extract_odt(self, doc, odf_text) -> str:
        """Extract text from an ODT document in document order."""
        lines: list[str] = []
        body = doc.body
        for child in body.childNodes:
            tag = getattr(child, "qname", None)
            if tag is None:
                continue
            # Check for heading elements.
            h_qname = odf_text.H().qname
            p_qname = odf_text.P().qname
            if tag == h_qname:
                text = self._get_text(child)
                if text.strip():
                    lines.append(f"## {text.strip()}")
                    lines.append("")
            elif tag == p_qname:
                text = self._get_text(child)
                if text.strip():
                    lines.append(text.strip())
                    lines.append("")
        return "\n".join(lines)

    def _extract_ods(self, doc, odf_table) -> str:
        """Extract tables from an ODS document as Markdown."""
        output: list[str] = []
        tables = doc.getElementsByType(odf_table.Table)
        for table in tables:
            name_attr = table.getAttribute("name")
            if name_attr:
                output.append(f"### {name_attr}")
                output.append("")
            rows = table.getElementsByType(odf_table.TableRow)
            table_data: list[list[str]] = []
            for row in rows:
                cells = row.getElementsByType(
                    odf_table.TableCell
                )
                row_data: list[str] = []
                for cell in cells:
                    row_data.append(self._get_text(cell).strip())
                table_data.append(row_data)
            if table_data:
                output.extend(
                    self._format_markdown_table(table_data)
                )
                output.append("")
        return "\n".join(output)

    @staticmethod
    def _format_markdown_table(
        rows: list[list[str]],
    ) -> list[str]:
        """Format a 2-D list of strings as a Markdown table."""
        if not rows:
            return []
        header = rows[0]
        lines: list[str] = []
        lines.append("| " + " | ".join(header) + " |")
        lines.append(
            "| " + " | ".join("---" for _ in header) + " |"
        )
        for row in rows[1:]:
            # Pad row to match header length.
            padded = row + [""] * (len(header) - len(row))
            lines.append("| " + " | ".join(padded) + " |")
        return lines

    def _extract_odp(self, doc, odf_text) -> str:
        """Extract text frames from an ODP presentation."""
        lines: list[str] = []
        slide_num = 0
        # ODP uses draw:page elements; each page is a slide.
        try:
            from odf import draw as odf_draw
            pages = doc.getElementsByType(odf_draw.Page)
        except (ImportError, AttributeError):
            pages = []

        for page in pages:
            slide_num += 1
            lines.append(f"## Slide {slide_num}")
            lines.append("")
            for elem in page.getElementsByType(odf_text.P):
                text = self._get_text(elem)
                if text.strip():
                    lines.append(text.strip())
            lines.append("")
        return "\n".join(lines)

    # ----------------------------------------------------------------
    # LibreOffice fallback
    # ----------------------------------------------------------------

    def _parse_with_libreoffice(
        self, file_path: str, ext: str, **kwargs
    ) -> ParseResult:
        """Convert via LibreOffice headless then delegate."""
        # Map ODF → modern format for conversion target.
        target_map = {
            ".odt": "docx",
            ".ods": "xlsx",
            ".odp": "pptx",
        }
        target_fmt = target_map.get(ext, "docx")

        with secure_temp_dir() as td_name:
            abs_path = os.path.abspath(file_path)
            lo_profile = os.path.join(td_name, "lo-profile")
            os.makedirs(lo_profile, exist_ok=True)
            write_lo_profile_security(lo_profile)

            args = [
                "libreoffice",
                "--headless",
                "--norestore",
                "--nologo",
                "--nodefault",
                "--nofirststartwizard",
                f"-env:UserInstallation=file://{lo_profile}",
                "--convert-to",
                target_fmt,
                "--outdir",
                td_name,
                abs_path,
            ]

            run_libreoffice_with_lock(
                args, timeout=LIBREOFFICE_TIMEOUT
            )

            # Find the converted file.
            basename = os.path.splitext(
                os.path.basename(file_path)
            )[0]
            converted = os.path.join(
                td_name, f"{basename}.{target_fmt}"
            )
            if not os.path.isfile(converted):
                raise ParseError(
                    "LibreOffice conversion produced no output file.",
                    detail=f"Expected: {converted}",
                )

            # Delegate to MarkItDown.
            from cobots_lib.docparse.handlers.markitdown_handler import (
                MarkItDownHandler,
            )

            md_handler = MarkItDownHandler()
            result = md_handler.parse(converted, **kwargs)
            return ParseResult(
                content=result.content,
                output_format=result.output_format,
                source_path=file_path,
                source_format=ext,
                handler_name=f"{self.name} (via LibreOffice)",
                metadata=result.metadata,
                warnings=result.warnings,
            )

    # ----------------------------------------------------------------
    # Dependency checks
    # ----------------------------------------------------------------

    @staticmethod
    def _has_odfpy() -> bool:
        try:
            import odf  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def _has_libreoffice() -> bool:
        return shutil.which("libreoffice") is not None
