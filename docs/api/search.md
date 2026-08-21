# Search

`GET /api/search` accepts `q`, `author`, `date_from`, `date_to`, `sort=relevance|date`, `direction=asc|desc`, `limit=1..50` and `offset=0..10000`. Elasticsearch searches comment text and author fields, supports fuzzy full-text matching and case-insensitive author-name/email substrings, applies date filters and returns text highlights. Responses include `next_offset`; a null value marks the final page.

PostgreSQL remains authoritative. When Elasticsearch cannot be reached, the endpoint performs a reduced `icontains` search and reports `source=postgresql`. Run `python manage.py rebuild_search_index` to recreate the entire index from PostgreSQL.
