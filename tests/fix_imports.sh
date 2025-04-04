#!/bin/bash
# Script to fix imports in all test files

echo "Fixing import statements in test files..."

# Replace 'from backend' with 'from src'
find . -type f -name "*.py" -exec grep -l "from backend" {} \; | xargs sed -i "" "s/from backend/from src/g"

# Replace 'import backend' with 'import src'
find . -type f -name "*.py" -exec grep -l "import backend" {} \; | xargs sed -i "" "s/import backend/import src/g"

# Handle direct imports from modules (e.g., from ollama_client import X)
# These need special handling to add the proper path

# List of modules to check
modules=(
  "ollama_client:src.ai.companion.tier2.ollama_client"
  "config:src.ai.companion.config"
  "intent_classifier:src.ai.companion.core.intent_classifier"
  "models:src.ai.companion.core.models"
  "profile:src.ai.companion.core.npc.profile"
  "profile_loader:src.ai.companion.core.npc.profile_loader"
  "response_formatter:src.ai.companion.core.response_formatter"
  "prompt_manager:src.ai.companion.core.prompt_manager"
  "request_handler:src.ai.companion.core.request_handler"
  "bedrock_client:src.ai.companion.tier3.bedrock_client"
  "tier1_processor:src.ai.companion.tier1.tier1_processor"
  "tier2_processor:src.ai.companion.tier2.tier2_processor"
  "tier3_processor:src.ai.companion.tier3.tier3_processor"
)

for module_pair in "${modules[@]}"; do
  module_name=${module_pair%%:*}
  module_path=${module_pair#*:}
  
  echo "Fixing imports for $module_name -> $module_path"
  
  # Update: from module_name import X
  find . -type f -name "*.py" -exec grep -l "from $module_name import" {} \; | xargs sed -i "" "s/from $module_name import/from $module_path import/g"
  
  # Update: import module_name
  find . -type f -name "*.py" -exec grep -l "import $module_name" {} \; | xargs sed -i "" "s/import $module_name$/import $module_path/g"
done

echo "Import fixes completed." 