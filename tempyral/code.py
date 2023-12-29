from typing import Dict, List, Literal, Set, Tuple

from tempyral.entity import Entity

Language = Literal["go", "python", "typescript", "java", "dotnet"]


COMMENT_MARKERS: Dict[Language, str] = {
    "go": "//",
    "java": "//",
    "python": "#",
    "dotnet": "//",
}


class EntityWithCode(Entity):
    language: Language
    go: str
    code: str
    blocked_expressions: Set[int]

    def __init__(self, *args, **kwargs):
        if not hasattr(self, "language"):
            self.language = self._get_language()
        super().__init__(*args, **kwargs)

    def _get_language(self) -> Language:
        available_languages = list(COMMENT_MARKERS)
        languages: List[Language] = [l for l in available_languages if hasattr(self, l)]
        assert (
            languages
        ), f"You must define the workflow code as a class attribute named one of {', '.join(available_languages)}"
        assert (
            len(languages) == 1
        ), "You must set the 'language' class attribute when supplying workflow code in multiple languages"
        [language] = languages
        return language

    def parse_code(self, language: Language) -> Tuple[str, List[Tuple[str, int]]]:
        """
        Return code, and list of commands.

        Strip out special WFT-handling directives, and convert these into the
        corresponding Command, together with line number.
        """
        lines: List[str] = []
        directives: List[Tuple[str, int]] = []
        comment_marker = COMMENT_MARKERS[language]
        code = getattr(self, language)
        line_num = 1
        for line_num, line in enumerate(code.strip().splitlines(), line_num):
            code, _, directive = line.partition(f"{comment_marker} tempyral:")
            if directive:
                directives.append((directive.strip(), line_num))
            lines.append(code)
        return "\n".join(lines), directives
