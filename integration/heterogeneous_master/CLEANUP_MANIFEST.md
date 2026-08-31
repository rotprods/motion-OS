# P3.3 integration-tree cleanup

The final PR tree must retain only semantic integration artifacts (`README.md`, `IMPORT_MANIFEST.json`, `SOURCE_LINEAGE.json`) and executable/runtime evidence. Connector-routing staging markers are historical audit noise, carry zero authority, and are removed from the final tree. Their history remains recoverable in Git.
