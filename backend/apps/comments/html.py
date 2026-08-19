import html
from html.parser import HTMLParser

import nh3
from rest_framework import serializers

ALLOWED_TAGS = {"a", "code", "i", "strong"}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}


class _AllowedTagValidator(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ALLOWED_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ALLOWED_TAGS:
            raise serializers.ValidationError("Allowed formatting tags cannot be self-closing.")

    def handle_endtag(self, tag: str) -> None:
        if tag not in ALLOWED_TAGS:
            return
        if not self.stack or self.stack.pop() != tag:
            raise serializers.ValidationError(
                "Formatting tags must be correctly nested and closed."
            )

    def validate(self, value: str) -> None:
        self.feed(value)
        self.close()
        if self.stack:
            raise serializers.ValidationError(
                "Formatting tags must be correctly nested and closed."
            )


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def sanitize_comment_html(value: str) -> tuple[str, str]:
    _AllowedTagValidator().validate(value)
    sanitized = nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        clean_content_tags={"script", "style"},
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="nofollow noopener noreferrer",
    )
    extractor = _TextExtractor()
    extractor.feed(sanitized)
    search_text = html.unescape("".join(extractor.parts)).strip()
    if not search_text:
        raise serializers.ValidationError("Comment text cannot be empty.")
    return sanitized, search_text
