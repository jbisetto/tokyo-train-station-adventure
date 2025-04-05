#!/bin/bash
find . -type f -name "*.py" -exec grep -l "import " {} \; | xargs sed -i "" "s/from backend\./from src./g"
find . -type f -name "*.py" -exec grep -l "import backend\." {} \; | xargs sed -i "" "s/import backend\./import src./g"
