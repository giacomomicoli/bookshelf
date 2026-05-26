# Book Domain

## Book Fields

- `id`: UUID
- `name`: required string
- `category`: required category reference
- `sub_category`: optional sub-category reference
- `purchase_urls`: JSON array of strings
- `thumbnail_object_key`: optional MinIO object key
- `thumbnail_source_url`: optional original remote URL
- `published_on`: optional full date
- `edition`: optional string
- `format`: optional controlled value
- `page_length`: optional integer
- `reading_status`: one of `unread`, `reading`, `read`
- `note`: optional long-form text
- `created_at`: timestamp
- `updated_at`: timestamp

## Rules

- `sub_category` is optional in all cases.
- If `sub_category` is provided, it must belong to the selected category.
- Purchase URLs are stored on the book record as JSON.
- Thumbnails are imported into object storage rather than stored as raw database blobs.
- Deleting a book also removes its stored thumbnail object.
- Replacing or clearing a thumbnail removes the previous stored thumbnail object after a successful update.
