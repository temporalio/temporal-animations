from typing import Literal

Language = Literal["go", "python", "typescript", "java", "dotnet"]


COMMENT_MARKERS: dict[Language, str] = {
    "dotnet": "//",
    "go": "//",
    "java": "//",
    "python": "#",
    "typescript": "//",
}


class WithCode:
    language: Language
    go: str
    typescript: str
    code: str
    blocked_lines: set[int]

    __publish__ = {
        "code",
        "language",
        "blocked_lines",
        "active",
    }

    def _get_language(self) -> Language:
        available_languages = list(COMMENT_MARKERS)
        languages: list[Language] = [l for l in available_languages if hasattr(self, l)]
        assert (
            languages
        ), f"You must define the workflow code as a class attribute named one of {', '.join(available_languages)}"
        assert (
            len(languages) == 1
        ), "You must set the 'language' class attribute when supplying workflow code in multiple languages"
        [language] = languages
        return language

    def parse_code(self, language: Language) -> tuple[str, list[tuple[list[str], int]]]:
        """
        Strip directives; return code, and list of directives with line numbers.
        """
        lines: list[str] = []
        directives: list[tuple[list[str], int]] = []
        comment_marker = COMMENT_MARKERS[language]
        code: str = getattr(self, language)
        line_num = 1
        for line_num, line in enumerate(code.strip().splitlines(), line_num):
            code, _, directive = line.partition(f"{comment_marker} tempyral:")
            if directive:
                directives.append((directive.strip().split(), line_num))
            lines.append(code.rstrip())
        return "\n".join(lines), directives
