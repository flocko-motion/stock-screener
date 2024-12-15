#!/bin/bash

## Compress all PNG files in a directory using pngquant
## Then move the original files to a backup directory
## and use the compressed files in the original directory

# Directory containing PNG files
IMAGE_DIR="./html/plots"

# Create a backup directory for original images
BACKUP_DIR="./backup/plots"
mkdir -p "$BACKUP_DIR"

# Create a compressed directory for smaller files
COMPRESSED_DIR="./html/plots-compressed"
mkdir -p "$COMPRESSED_DIR"

# Iterate over all PNG files in the directory
for img in "$IMAGE_DIR"/*.png; do
    # Skip if no files found
    [ -e "$img" ] || continue

    # Copy original image to backup directory
    cp "$img" "$BACKUP_DIR"

    # Compress the image with pngquant (adjust quality as needed)
    pngquant --quality=65-80 --force "$img" --output "$COMPRESSED_DIR/$(basename "$img")"

    echo "Compressed: $(basename "$img")"
done

mv "$IMAGE_DIR"/*.png "$BACKUP_DIR"
mv "$COMPRESSED_DIR"/*.png "$IMAGE_DIR"
rmdir "$COMPRESSED_DIR"

echo "All PNG files have been compressed and saved to $COMPRESSED_DIR."
