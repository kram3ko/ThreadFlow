# Search

`GET /api/search` accepts `q`, `author`, `date_from`, `date_to`, `sort=relevance|date` and `direction=asc|desc`. Elasticsearch searches comment text and author fields, supports fuzzy matching, applies date filters and returns text highlights.

PostgreSQL remains authoritative. When Elasticsearch cannot be reached, the endpoint performs a reduced `icontains` search and reports `source=postgresql`. Run `python manage.py rebuild_search_index` to recreate the entire index from PostgreSQL.
