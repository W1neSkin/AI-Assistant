#!/bin/bash

# Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.py[co]" -delete

echo "Cleanup complete!" 