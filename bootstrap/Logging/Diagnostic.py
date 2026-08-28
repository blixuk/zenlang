import os
import sys
from typing import List, Optional, Dict, Any

RED = "\033[1;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
WHITE = "\033[1;37m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

class SourceCache:
    """Caches source files in memory for fast diagnostic context retrieval."""
    _cache: Dict[str, List[str]] = {}

    @classmethod
    def get_lines(cls, file_path: str) -> List[str]:
        if not file_path:
            return []
        norm_path = os.path.abspath(file_path) if os.path.exists(file_path) else file_path
        if norm_path not in cls._cache:
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                        cls._cache[norm_path] = f.read().splitlines()
                except Exception:
                    cls._cache[norm_path] = []
            else:
                cls._cache[norm_path] = []
        return cls._cache[norm_path]

    @classmethod
    def set_source(cls, file_path: str, source_text: str):
        if file_path and source_text is not None:
            norm_path = os.path.abspath(file_path) if os.path.exists(file_path) else file_path
            cls._cache[norm_path] = source_text.splitlines()

    @classmethod
    def get_line(cls, file_path: str, line_num: int) -> Optional[str]:
        lines = cls.get_lines(file_path)
        if 1 <= line_num <= len(lines):
            return lines[line_num - 1]
        return None


class Span:
    """Represents a source code span with file, line, column, and length."""
    def __init__(
        self,
        file: str,
        line: int,
        column: int,
        length: int = 1,
        label: Optional[str] = None
    ):
        self.file = file or "unknown"
        self.line = line if line is not None and line > 0 else 1
        self.column = column if column is not None and column > 0 else 1
        self.length = max(1, length if length is not None else 1)
        self.label = label

    @classmethod
    def from_token(cls, token: Any, file: Optional[str] = None, label: Optional[str] = None) -> "Span":
        if token is None:
            return cls(file or "unknown", 1, 1, 1, label)
        t_file = getattr(token, "filename", None) or file or "unknown"
        t_line = getattr(token, "line", 1)
        t_col = getattr(token, "column", 1)
        t_val = getattr(token, "value", "")
        t_len = len(str(t_val)) if t_val else 1
        return cls(t_file, t_line, t_col, t_len, label)

    @classmethod
    def from_node(cls, node: Any, file: Optional[str] = None, label: Optional[str] = None) -> "Span":
        if node is None:
            return cls(file or "unknown", 1, 1, 1, label)
        n_file = getattr(node, "filename", None) or file or "unknown"
        n_line = getattr(node, "line", 1)
        n_col = getattr(node, "column", 1)
        n_val = getattr(node, "name", None) or getattr(node, "value", None) or ""
        n_len = len(str(n_val)) if n_val else 1
        return cls(n_file, n_line, n_col, n_len, label)


class DiagnosticSeverity:
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"
    HELP = "help"


class Diagnostic:
    """Structured compiler diagnostic."""
    def __init__(
        self,
        severity: str,
        message: str,
        code: Optional[str] = None,
        span: Optional[Span] = None,
        hints: Optional[List[str]] = None,
        notes: Optional[List[str]] = None
    ):
        self.severity = severity
        self.message = message
        self.code = code
        self.span = span
        self.hints = hints or []
        self.notes = notes or []

    @classmethod
    def error(cls, message: str, code: Optional[str] = None, span: Optional[Span] = None) -> "Diagnostic":
        return cls(DiagnosticSeverity.ERROR, message, code, span)

    @classmethod
    def warning(cls, message: str, code: Optional[str] = None, span: Optional[Span] = None) -> "Diagnostic":
        return cls(DiagnosticSeverity.WARNING, message, code, span)

    def add_hint(self, hint: str) -> "Diagnostic":
        self.hints.append(hint)
        return self

    def add_note(self, note: str) -> "Diagnostic":
        self.notes.append(note)
        return self

    def render(self, use_color: bool = True) -> str:
        return DiagnosticRenderer.render(self, use_color=use_color)

    def to_zendata(self) -> str:
        """Serializes diagnostic to Zen Data (.zd) format."""
        lines = ["Diagnostic {"]
        lines.append(f"    severity -> \"{self.severity}\",")
        if self.code:
            lines.append(f"    code -> \"{self.code}\",")
        lines.append(f"    message -> \"{self.message}\",")
        if self.span:
            lines.append("    span -> {")
            lines.append(f"        file -> \"{self.span.file}\",")
            lines.append(f"        line -> {self.span.line},")
            lines.append(f"        column -> {self.span.column},")
            lines.append(f"        length -> {self.span.length}")
            lines.append("    },")
        if self.hints:
            hint_strs = ", ".join(f'"{h}"' for h in self.hints)
            lines.append(f"    hints -> [{hint_strs}],")
        if self.notes:
            note_strs = ", ".join(f'"{n}"' for n in self.notes)
            lines.append(f"    notes -> [{note_strs}],")
        lines.append("}")
        return "\n".join(lines)

    def to_zenmark(self) -> str:
        """Serializes diagnostic to Zen Mark (.zm) Callout format."""
        callout_type = "caution" if self.severity == DiagnosticSeverity.ERROR else "warning"
        title = f"{self.severity}[{self.code or 'Diagnostic'}]: {self.message}"
        text_lines = []
        if self.span:
            text_lines.append(f"In **{self.span.file}:{self.span.line}:{self.span.column}**:\n")
            line_content = SourceCache.get_line(self.span.file, self.span.line)
            if line_content is not None:
                text_lines.append("```zen")
                text_lines.append(line_content)
                carets = " " * (self.span.column - 1) + "^" * self.span.length
                if self.span.label:
                    carets += f" {self.span.label}"
                text_lines.append(carets)
                text_lines.append("```\n")
        for hint in self.hints:
            text_lines.append(f"**Help:** {hint}\n")
        for note in self.notes:
            text_lines.append(f"**Note:** {note}\n")

        inner_text = "\n".join(text_lines)
        return f'Callout {{\n    type -> "{callout_type}",\n    title -> "{title}",\n    text -> "{inner_text}"\n}}'


class DiagnosticRenderer:
    """Renders high-clarity source code frames with carets, line numbering, and colors."""

    @staticmethod
    def render(diag: Diagnostic, use_color: bool = True) -> str:
        c_red = RED if use_color else ""
        c_yellow = YELLOW if use_color else ""
        c_blue = BLUE if use_color else ""
        c_cyan = CYAN if use_color else ""
        c_white = WHITE if use_color else ""
        c_dim = DIM if use_color else ""
        c_bold = BOLD if use_color else ""
        c_reset = RESET if use_color else ""

        sev_color = c_red if diag.severity == DiagnosticSeverity.ERROR else c_yellow
        code_suffix = f"[{diag.code}]" if diag.code else ""
        header = f"{sev_color}{c_bold}{diag.severity}{code_suffix}{c_reset}: {c_bold}{diag.message}{c_reset}"

        if not diag.span or not diag.span.file or diag.span.file == "unknown":
            res = [header]
            for note in diag.notes:
                res.append(f"{c_cyan}   = note:{c_reset} {note}")
            for hint in diag.hints:
                res.append(f"{c_cyan}   = help:{c_reset} {hint}")
            return "\n".join(res)

        span = diag.span
        file_loc = f"{c_cyan}  --> {c_reset}{span.file}:{span.line}:{span.column}"

        lines = SourceCache.get_lines(span.file)
        if not lines or span.line > len(lines):
            res = [header, file_loc]
            for note in diag.notes:
                res.append(f"{c_cyan}   = note:{c_reset} {note}")
            for hint in diag.hints:
                res.append(f"{c_cyan}   = help:{c_reset} {hint}")
            return "\n".join(res)

        start_line = max(1, span.line - 1)
        end_line = min(len(lines), span.line + 1)
        gutter_width = len(str(end_line)) + 1
        gutter_pad = " " * gutter_width

        output = [header, file_loc, f"{c_blue}{gutter_pad}|{c_reset}"]

        for cur_line_num in range(start_line, end_line + 1):
            line_str = lines[cur_line_num - 1]
            expanded_line = line_str.replace("\t", "    ")
            num_str = str(cur_line_num).rjust(gutter_width - 1)

            if cur_line_num == span.line:
                output.append(f"{c_blue}{num_str} |{c_reset} {expanded_line}")
                
                # Compute visual column considering tab expansion
                prefix = line_str[:span.column - 1]
                visual_col = len(prefix.replace("\t", "    "))
                caret_len = max(1, span.length)
                
                carets = "^" * caret_len
                label_str = f" {span.label}" if span.label else ""
                output.append(f"{c_blue}{gutter_pad}|{c_reset} {' ' * visual_col}{sev_color}{c_bold}{carets}{label_str}{c_reset}")
            else:
                output.append(f"{c_dim}{num_str} |{c_reset} {expanded_line}")

        output.append(f"{c_blue}{gutter_pad}|{c_reset}")

        for note in diag.notes:
            output.append(f"{c_cyan}{gutter_pad}= note:{c_reset} {note}")
        for hint in diag.hints:
            output.append(f"{c_cyan}{gutter_pad}= help:{c_reset} {hint}")

        return "\n".join(output)
