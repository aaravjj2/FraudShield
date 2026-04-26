#!/bin/bash

echo "🔍 Validating FraudShield Dashboard..."

echo "✓ Checking file structure..."
files=(
  "package.json"
  "vite.config.ts"
  "tsconfig.json"
  "index.html"
  "src/main.tsx"
  "src/App.tsx"
  "src/types.ts"
  "src/api.ts"
  "src/components/StatsBar.tsx"
  "src/components/TransactionFeed.tsx"
  "src/components/TestForm.tsx"
  "src/components/ShapDrawer.tsx"
  "src/App.css"
  "Dockerfile"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "  ✓ $file"
  else
    echo "  ✗ $file (missing)"
    exit 1
  fi
done

echo "✓ Checking data-testid attributes..."
testids=(
  "transaction-feed"
  "fraud-row"
  "legit-row"
  "shap-drawer"
  "shap-bar"
  "amount-input"
  "v1-input"
  "v2-input"
  "submit-btn"
  "stats-bar"
)

for testid in "${testids[@]}"; do
  if grep -r "data-testid=\"$testid\"" src/ > /dev/null 2>&1; then
    echo "  ✓ $testid"
  else
    echo "  ✗ $testid (not found)"
    exit 1
  fi
done

echo "✓ Checking TypeScript compilation..."
if npm run build > /dev/null 2>&1; then
  echo "  ✓ TypeScript compilation successful"
else
  echo "  ✗ TypeScript compilation failed"
  exit 1
fi

echo "✓ Checking production build..."
if [ -d "dist" ]; then
  echo "  ✓ Production build exists"
  if [ -f "dist/index.html" ]; then
    echo "  ✓ index.html present"
  fi
else
  echo "  ✗ Production build missing"
  exit 1
fi

echo ""
echo "🎉 Dashboard validation complete! All checks passed."
echo ""
echo "📋 Summary:"
echo "  • All required files present"
echo "  • All data-testid attributes found"
echo "  • TypeScript compilation successful"
echo "  • Production build ready"
echo ""
echo "🚀 Next steps:"
echo "  1. Start backend: cd .. && python -m uvicorn api.main:app --reload"
echo "  2. Start dashboard: npm run dev"
echo "  3. Open browser: http://localhost:3000"
