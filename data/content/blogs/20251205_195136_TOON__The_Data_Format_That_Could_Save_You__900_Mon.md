---
title: "TOON: The Data Format That Could Save You $900/Month on LLM API Costs"
target_audience: TargetAudienceEnum.PRACTITIONER
tone: professional
tags: []
reading_time: "Unknown"
created_at: "2025-12-05T19:51:36.723420"
status: ready
---

# TOON: The Data Format That Could Save You $900/Month on LLM API Costs

If you're building LLM-powered applications at scale, you've probably experienced that sinking feeling when reviewing your monthly API bills. Every bracket, comma, and quote in your JSON payloads is costing you money—literally. A typical production application processing structured data through GPT-4 or Claude can burn through thousands of dollars monthly, with a significant portion of that cost coming from... formatting.

Enter Token-Oriented Object Notation (TOON), a specialized data serialization format introduced in 2025 that achieves 30-60% token reduction compared to JSON while maintaining complete lossless compatibility. For practitioners working with LLMs at scale, TOON isn't just an interesting technical curiosity—it's a practical tool that can translate directly to reduced operational costs and improved performance.

---

## The Token Tax: Why JSON Is Expensive for LLMs

Let's start with the fundamental problem. When you send data to an LLM, every single character gets tokenized and billed. Consider this simple JSON array of user records:

```json
[
  {"id": 1, "name": "Alice", "role": "admin", "active": true},
  {"id": 2, "name": "Bob", "role": "user", "active": true},
  {"id": 3, "name": "Carol", "role": "user", "active": false}
]
```

Notice what's happening here? The keys `"id"`, `"name"`, `"role"`, and `"active"` are repeated three times. Every quote mark, colon, comma, and brace is a billable token. For three records, this might seem trivial. But scale this to 1,000 records, and you're paying for 1,000 repetitions of the same structural information.

The mathematics are sobering. For an array of N objects with K keys averaging 6 characters each, JSON wastes approximately:

```
Saved_Tokens ≈ (N - 1) × K × (Avg_Key_Length + 4)
```

For 100 objects with 5 keys: `99 × 5 × 10 = 4,950 tokens` of pure overhead. At typical pricing of $0.01 per 1K tokens, processing one million such requests monthly costs an extra $900 just for repeated keys.

---

## How TOON Works: Tabular Arrays as the Core Innovation

TOON's breakthrough is deceptively simple: when you have an array of uniform objects (same keys, same order, only primitive values), declare the keys once and then list just the values. Here's that same user data in TOON format:

```toon
users[3]:
  id, name, role, active
  1, Alice, admin, true
  2, Bob, user, true
  3, Carol, user, false
```

The transformation is dramatic. Instead of repeating `"id":`, `"name":`, `"role":`, and `"active":` for every record, TOON declares them once in a header row. The result looks like a CSV table but maintains JSON's full expressiveness through intelligent encoding strategies.

### The Tabular Detection Algorithm

TOON's encoder automatically identifies arrays that qualify for tabular optimization. The algorithm performs three checks:

1. **All elements are objects** (not primitives or arrays)
2. **All objects have identical keys in the same order**
3. **All values are primitives** (strings, numbers, booleans, null)

Here's the core detection logic in JavaScript:

```javascript
function isTabularArray(arr) {
  if (!Array.isArray(arr) || arr.length === 0) return false;
  
  const first = arr[0];
  if (typeof first !== 'object' || Array.isArray(first) || first === null) {
    return false;
  }
  
  const keys = Object.keys(first).sort();
  
  for (const elem of arr) {
    const elemKeys = Object.keys(elem).sort();
    if (elemKeys.length !== keys.length) return false;
    
    for (let i = 0; i < keys.length; i++) {
      if (keys[i] !== elemKeys[i]) return false;
    }
    
    for (const val of Object.values(elem)) {
      if (typeof val === 'object' && val !== null) return false;
    }
  }
  
  return true;
}
```

When this test passes, TOON applies tabular encoding. When it fails, TOON falls back to other optimization strategies while still reducing tokens compared to JSON.

---

## Beyond Tabular: TOON's Complete Encoding Strategy

TOON isn't just about tables. It employs different optimization techniques based on data structure:

### 1. Indentation-Based Nesting

For complex objects, TOON uses Python-style indentation instead of curly braces:

```toon
user:
  id: 42
  profile:
    name: Alice
    email: alice@example.com
  settings:
    theme: dark
    notifications: true
```

This eliminates `{`, `}`, and many quotes while maintaining perfect readability.

### 2. Primitive Arrays

Arrays of simple values use inline comma separation:

```toon
tags[4]: javascript, python, react, node
```

No brackets, no quotes (when unnecessary), maximum compactness.

### 3. List Format for Heterogeneous Arrays

When array elements have different structures, TOON uses dash prefixes:

```toon
mixed[3]:
  - type: user, id: 1
  - type: group, id: 5, members: 12
  - type: admin, id: 3, permissions: all
```

This maintains structure while still reducing overhead compared to JSON's verbose syntax.

### 4. Configurable Delimiters

TOON supports comma, tab, and pipe delimiters. The choice matters because tokenizers treat them differently:

```toon
# Comma (default)
users[2]:
  id, name, score
  1, Alice, 95
  
# Tab (often single token)
users[2]:
  id	name	score
  1	Alice	95
  
# Pipe (better when data contains commas)
users[2]:
  id | name | score
  1 | Alice | 95
```

Tab delimiters can provide additional 5-10% savings with some tokenizers like GPT-4's.

---

## Production Implementation: Getting Started

### JavaScript/TypeScript Integration

Install the official package:

```bash
npm install @toon-format/toon
```

Basic encoding and decoding:

```javascript
import { encode, decode } from '@toon-format/toon';

const data = {
  logs: [
    { timestamp: 1234567890, level: 'error', message: 'Connection timeout' },
    { timestamp: 1234567891, level: 'warn', message: 'Retry attempt 1' },
    { timestamp: 1234567892, level: 'info', message: 'Connection restored' }
  ]
};

// Convert to TOON
const toonData = encode(data);

// Send to LLM
const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'system', content: 'Analyze these logs in TOON format' },
    { role: 'user', content: toonData }
  ]
});

// Convert back if needed
const jsonData = decode(toonData);
```

### Measuring Token Savings

Always validate savings for your specific data:

```javascript
import { encoding_for_model } from 'tiktoken';
import { encode } from '@toon-format/toon';

function compareTokenCounts(data, model = 'gpt-4o-mini') {
  const tokenizer = encoding_for_model(model);
  
  const jsonStr = JSON.stringify(data);
  const toonStr = encode(data);
  
  const jsonTokens = tokenizer.encode(jsonStr).length;
  const toonTokens = tokenizer.encode(toonStr).length;
  
  const savings = ((jsonTokens - toonTokens) / jsonTokens) * 100;
  
  console.log(`JSON tokens: ${jsonTokens}`);
  console.log(`TOON tokens: ${toonTokens}`);
  console.log(`Savings: ${savings.toFixed(2)}%`);
  
  tokenizer.free();
  
  return { jsonTokens, toonTokens, savings };
}
```

### Python Implementation

For Python-based workflows:

```bash
pip install python-toon
```

```python
from toon import encode, decode
import openai

# Fetch structured data
logs = fetch_logs_from_database()

# Convert to TOON
toon_formatted = encode(logs, delimiter='\t', indent=2)

# Send to LLM
response = openai.ChatCompletion.create(
    model='gpt-4',
    messages=[
        {'role': 'system', 'content': 'Analyze these logs'},
        {'role': 'user', 'content': toon_formatted}
    ]
)

# Parse response
result = decode(response.choices[0].message.content)
```

---

## Real-World Use Cases: Where TOON Shines

### Log Analysis

Application logs are perfect for TOON. They're typically arrays of uniform objects with consistent fields:

```toon
logs[1000]:
  timestamp, level, service, message, user_id
  1704067200, error, api, Connection timeout, 12345
  1704067201, warn, api, Retry attempt 1, 12345
  1704067202, info, api, Success, 12345
  ...
```

**Typical savings**: 50-60% token reduction for log batches.

### Database Query Results

SQL query results convert beautifully to tabular TOON:

```toon
users[50]:
  id, email, created_at, subscription_tier, mrr
  1001, user1@example.com, 2024-01-15, premium, 99
  1002, user2@example.com, 2024-01-16, basic, 9
  ...
```

**Typical savings**: 45-55% token reduction.

### API Response Aggregation

When aggregating multiple API responses for LLM analysis:

```toon
api_metrics[24]:
  hour, requests, avg_latency_ms, error_rate, p95_latency
  0, 15234, 45, 0.02, 120
  1, 12456, 42, 0.01, 115
  ...
```

**Typical savings**: 40-50% token reduction.

### Batch Processing

Processing batches of structured records for classification, extraction, or transformation:

```toon
customer_feedback[200]:
  id, date, rating, category, resolved
  5001, 2024-01-15, 4, billing, true
  5002, 2024-01-15, 2, technical, false
  ...
```

**Typical savings**: 50-65% token reduction.

---

## Production Best Practices

### 1. Implement at the API Boundary

Keep your application code using standard JSON. Convert to TOON only when sending to LLMs:

```javascript
// Your application logic uses JSON
const data = await database.query('SELECT * FROM logs');

// Convert to TOON at the API boundary
const toonData = encode(data);
const llmResponse = await callLLM(toonData);

// Continue with JSON internally
const result = JSON.parse(llmResponse);
```

This approach maintains code maintainability while optimizing where it counts.

### 2. Cache Encoded Strings

If you're sending the same structure repeatedly:

```javascript
const encodingCache = new Map();

function getCachedEncoding(data) {
  const key = JSON.stringify(data);
  if (!encodingCache.has(key)) {
    encodingCache.set(key, encode(data));
  }
  return encodingCache.get(key);
}
```

### 3. Monitor Encoding Latency

For large payloads, measure conversion overhead:

```javascript
function encodeWithMetrics(data) {
  const start = performance.now();
  const encoded = encode(data);
  const duration = performance.now() - start;
  
  if (duration > 100) {
    console.warn(`TOON encoding took ${duration}ms`);
  }
  
  return encoded;
}
```

### 4. Use Appropriate Delimiters

Test different delimiters for your specific data and LLM:

```javascript
const configs = [
  { delimiter: ',' },
  { delimiter: '\t' },
  { delimiter: ' | ' }
];

for (const config of configs) {
  const encoded = encode(data, config);
  const tokens = countTokens(encoded);
  console.log(`${config.delimiter}: ${tokens} tokens`);
}
```

### 5. Validate Lossless Conversion

In development, verify round-trip integrity:

```javascript
import { encode, decode } from '@toon-format/toon';
import { deepEqual } from 'assert';

function validateConversion(data) {
  const encoded = encode(data);
  const decoded = decode(encoded);
  deepEqual(data, decoded, 'Lossless conversion failed');
}
```

---

## When NOT to Use TOON

TOON isn't a universal replacement for JSON. Consider these scenarios:

### Small Payloads

For objects with fewer than 10 elements, encoding overhead exceeds savings:

```javascript
// Not worth it
const smallData = { user: { id: 1, name: 'Alice' } };
```

**Recommendation**: Use JSON for payloads under ~50 tokens.

### Highly Irregular Structures

When objects in arrays have completely different keys:

```javascript
// Poor TOON candidate
const irregular = [
  { type: 'user', id: 1, name: 'Alice' },
  { type: 'event', timestamp: 123, action: 'click' },
  { type: 'metric', value: 42, unit: 'ms' }
];
```

**Recommendation**: TOON provides minimal benefit here; stick with JSON.

### Real-Time Streaming

When latency is critical and you're processing individual