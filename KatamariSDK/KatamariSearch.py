import os
import tempfile
from typing inport *
from datetime import datetime
from whoosh.fields import ID, TEXT, NUMERIC, DATETIME, Schema
from whoosh.index import create_in, exists_in, open_dir
from whoosh.qparser import MultifieldParser, AndGroup
from whoosh.qparser.dateparse import DateParserPlugin

class KatamariSearch:
    """Search index integrated with MVCC."""

    def __init__(self, schema_fields: Optional[Dict[str, str]] = None, index_dir: Optional[str] = None):
        self.index_dir = index_dir or tempfile.mkdtemp()  # Use temporary directory for the index
        self.schema = self._create_schema(schema_fields)
        self.index = self._create_or_open_index()

    def _create_schema(self, fields: Dict[str, str]) -> Schema:
        """Create schema from fields."""
        schema_dict = {
            'id': ID(stored=True, unique=True),
            'timestamp': DATETIME(stored=True)
        }
        # Update schema with provided fields
        for field_name, field_type in fields.items():
            if field_type == 'TEXT':
                schema_dict[field_name] = TEXT(stored=True)
            elif field_type == 'NUMERIC':
                schema_dict[field_name] = NUMERIC(stored=True)
            elif field_type == 'DATETIME':
                schema_dict[field_name] = DATETIME(stored=True)
            else:
                raise ValueError(f"Unsupported field type: {field_type}")
        
        print(f"Schema fields: {list(schema_dict.keys())}")  # Debugging statement to show schema fields
        return Schema(**schema_dict)

    def _create_or_open_index(self):
        """Create or open the Whoosh index."""
        if not exists_in(self.index_dir):
            os.makedirs(self.index_dir, exist_ok=True)
            return create_in(self.index_dir, self.schema)
        else:
            return open_dir(self.index_dir)

    def _index_document(self, key, value, version, timestamp):
        """Immediately index a document after it's written."""
        with self.index.writer() as writer:
            document = {
                'id': key,
                'timestamp': datetime.utcfromtimestamp(timestamp),
                'version': version
            }
            document.update(value)
            writer.update_document(**document)

    async def search(self, query_str: str, tx_start_time: float, schema_fields: List[str]):
        """Search for documents with version-awareness (filter by timestamp)."""
        with self.index.searcher() as searcher:
            query = MultifieldParser(schema_fields, self.schema).parse(query_str)
            results = searcher.search(query, limit=None)

            # Filter results by transaction start time (version-awareness)
            filtered_results = [result for result in results if result['timestamp'] <= datetime.utcfromtimestamp(tx_start_time)]
            return filtered_results

    def close(self):
        """Close the index."""
        self.index.close()

