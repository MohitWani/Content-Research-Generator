# setup-hooks.sh
#!/bin/bash

echo "Setting up Git hooks..."
cp hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
echo "✅ Git pre-commit hook installed."
