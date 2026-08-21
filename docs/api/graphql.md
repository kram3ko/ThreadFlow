# GraphQL read API

`POST /graphql` and query-string `GET /graphql` expose read-only access to comment trees. Authentication, comment commands and file uploads are intentionally absent from the schema and remain in REST or WebSocket APIs.

Available root fields:

- `commentBranch(id, depth)` loads one complete root branch for any comment ID;
- `commentBranches(ids, depth)` batches up to 25 branches in one request;
- `rootComments(first, depth)` returns up to 25 newest root branches.

`depth` is bounded to `0..10`. The schema also limits aliases, parsed tokens and overall GraphQL query depth. A request-scoped DataLoader batches aliased or multi-branch reads, while PostgreSQL queries preload users, avatars and attachments.

```graphql
query Discussion($ids: [ID!]!) {
  commentBranches(ids: $ids, depth: 3) {
    id
    author {
      name
      email
      avatarUrl
    }
    htmlText
    attachments {
      kind
      originalName
      contentUrl
    }
    replies {
      id
      text
    }
  }
}
```
