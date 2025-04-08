# Database Migrations

This directory contains database migration scripts managed by Alembic.

## Usage

To create a new migration:

```bash
alembic revision --autogenerate -m "Description of your changes"
```

To apply migrations:

```bash
alembic upgrade head
```

To downgrade to a previous version:

```bash
alembic downgrade -1  # Go back one revision
```

or

```bash
alembic downgrade <revision_id>  # Go back to a specific revision
```

## Migration History

Migration history is stored in the `versions` directory.

## More Information

For more details on using Alembic, see the [Alembic documentation](https://alembic.sqlalchemy.org/).
