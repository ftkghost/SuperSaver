# Generated by Django 2.0.1 on 2018-06-06 05:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0001_initial'),
    ]

    operations = [
        # Add a trigger to update search vector whenever
        # https://www.postgresql.org/docs/current/static/textsearch-features.html#TEXTSEARCH-UPDATE-TRIGGERS
        migrations.RunSQL("""
            CREATE FUNCTION product_update_trigger() RETURNS trigger AS $$
            BEGIN
                IF old IS NOT NULL 
                  AND (new.title = old.title 
                    AND new.description = old.description 
                    AND new.landing_page = old.landing_page) THEN
                    return new;
                END IF;
                new.search_vector :=
                    setweight(to_tsvector('pg_catalog.english', coalesce(new.title, '')), 'A') ||
                    setweight(to_tsvector('pg_catalog.english', coalesce(new.description, '')), 'C') ||
                    setweight(to_tsvector('pg_catalog.english', coalesce(new.landing_page, '')), 'D');
                return new;
            END
            $$ LANGUAGE plpgsql;
            
            CREATE TRIGGER product_search_vector_update BEFORE INSERT OR UPDATE
                ON product_product FOR EACH ROW EXECUTE PROCEDURE product_update_trigger();
            """),
    ]
