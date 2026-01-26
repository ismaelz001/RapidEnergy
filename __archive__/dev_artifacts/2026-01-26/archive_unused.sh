#!/bin/bash
# archive_unused.sh - Move fixtures to archive

DATE=$(date +%Y_%m_%d)
ARCHIVE_DIR="__archive__/$DATE"

echo "Creating archive directory: $ARCHIVE_DIR"
mkdir -p "$ARCHIVE_DIR"

# Move fixtures
if [ -d "facturas" ]; then
    echo "Archiving facturas/..."
    mv facturas "$ARCHIVE_DIR/"
fi

if [ -f "facturas.zip" ]; then
    echo "Archiving facturas.zip..."
    mv facturas.zip "$ARCHIVE_DIR/"
fi

if [ -d "temp_facturas" ]; then
    echo "Archiving temp_facturas/..."
    mv temp_facturas "$ARCHIVE_DIR/"
fi

echo "Archiving complete. Check $ARCHIVE_DIR"
