from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont


class SQLHighlighter(QSyntaxHighlighter):
    """SQL syntax highlighter"""

    def __init__(self, document):
        super().__init__(document)
        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#00FF94"))
        keyword_format.setFontWeight(QFont.Weight.Bold)

        keywords = [
            "SELECT", "FROM", "WHERE", "INSERT", "UPDATE", "DELETE",
            "CREATE", "DROP", "ALTER", "TABLE", "INDEX", "VIEW",
            "JOIN", "INNER", "LEFT", "RIGHT", "OUTER", "FULL",
            "ON", "AND", "OR", "NOT", "IN", "EXISTS", "LIKE",
            "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET",
            "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MAX", "MIN",
            "UNION", "INTERSECT", "EXCEPT", "CASE", "WHEN", "THEN",
            "ELSE", "END", "NULL", "IS", "BETWEEN", "ASC", "DESC",
            "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "UNIQUE",
            "DEFAULT", "CHECK", "CONSTRAINT", "AUTO_INCREMENT",
            "AUTOINCREMENT", "INTEGER", "VARCHAR", "TEXT", "REAL",
            "BLOB", "NUMERIC", "DATE", "CURRENT_TIMESTAMP",
            "CURRENT_DATE", "CURRENT_TIME", "BOOLEAN", "INTO",
            "VALUES", "SET", "SHOW", "EXPLAIN", "DESCRIBE",
            "RELEASE", "SAVEPOINT", "ROLLBACK", "COMMIT", "BEGIN",
            "PRAGMA", "IF"
        ]

        for word in keywords:
            pattern = QRegularExpression(
                f"\\b{word}\\b",
                QRegularExpression.PatternOption.CaseInsensitiveOption
            )
            self.highlighting_rules.append((pattern, keyword_format))

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#7DD3FC"))

        # String patterns
        self.string_patterns = [
            QRegularExpression("'[^']*'"),
            QRegularExpression('"[^"]*"')
        ]

        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#FFA500"))
        self.number_pattern = QRegularExpression("\\b[0-9]+(?:\\.[0-9]+)?\\b")

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6B7280"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((
            QRegularExpression("--[^\n]*"), comment_format
        ))

        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#FBBF24"))
        self.highlighting_rules.append((
            QRegularExpression("\\b[A-Za-z_][A-Za-z0-9_]*(?=\\()"),
            function_format
        ))

    def highlightBlock(self, text):
        """Apply syntax highlighting to a block of text"""
        # Track which positions are inside strings
        string_ranges = []

        # First pass: Highlight strings and track their positions
        for pattern in self.string_patterns:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, self.string_format)
                string_ranges.append((start, start + length))

        # Second pass: Apply other rules, but skip string ranges
        for pattern, format_style in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                start = match.capturedStart()
                length = match.capturedLength()

                # Check if this match is inside a string
                inside_string = any(
                    s_start <= start < s_end
                    for s_start, s_end in string_ranges
                )

                if not inside_string:
                    self.setFormat(start, length, format_style)

        # Third pass: Highlight numbers (outside strings only)
        iterator = self.number_pattern.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            start = match.capturedStart()
            length = match.capturedLength()

            # Check if this number is inside a string
            inside_string = any(
                s_start <= start < s_end
                for s_start, s_end in string_ranges
            )

            if not inside_string:
                number_format = QTextCharFormat()
                number_format.setForeground(QColor("#FFA500"))
                self.setFormat(start, length, number_format)