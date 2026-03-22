# NEURON-X Omega — Integration Guide

## Python — Direct Usage (2 Lines)

```python
from neuronx import NeuronBrain

brain = NeuronBrain("my_brain")
brain.remember("I love eating pizza")
brain.remember("I work as a software engineer")

results = brain.recall("What food does user like?")
for engram, score in results:
    print(f"  [{engram.zone}] {engram.raw} (score={score:.3f})")

ctx = brain.get_context("Tell me about the user")
print(ctx.system_prompt_addition)

brain.end_session()
```

## OpenAI Integration

```python
from neuronx import NeuronBrain, OpenAIIntegration
import openai

brain = NeuronBrain("openai_memory")
integration = OpenAIIntegration(brain=brain, top_k=7)

messages = [{"role": "user", "content": "What do you know about me?"}]

# Inject memory context into messages
enriched = integration.pre_chat(messages)

# Send to OpenAI
response = openai.chat.completions.create(
    model="gpt-4", messages=enriched
)

# Store assistant response as memory
integration.post_chat(response.choices[0].message.content)
```

## Anthropic Integration

```python
from neuronx import NeuronBrain, AnthropicIntegration

brain = NeuronBrain("claude_memory")
integration = AnthropicIntegration(brain=brain)

messages = [{"role": "user", "content": "Hello!"}]
enriched = integration.pre_chat(messages)
# enriched[0] is system message with memory context
# Send to Claude API...
integration.post_chat(assistant_response)
```

## LangChain Integration

```python
from neuronx import NeuronBrain, LangChainIntegration

brain = NeuronBrain("langchain_memory")
integration = LangChainIntegration(brain=brain)

messages = [{"role": "user", "content": "My favorite color is blue"}]
enriched = integration.pre_chat(messages)
# Use with any LangChain LLM...
integration.post_chat(response_text)
```

## TypeScript SDK

```typescript
import { NeuronXClient } from 'neuronx-sdk';

const client = new NeuronXClient({
  baseUrl: 'http://localhost:8000',
});

// Store
await client.remember("I love pizza");

// Recall
const results = await client.recall("food");
console.log(results);

// Context for AI
const ctx = await client.getContext("Tell me about user");
console.log(ctx.system_prompt_addition);

// Real-time events
client.connectEvents((event) => {
  console.log('Event:', event.type, event.data);
});
```

## NRNLANG-Ω CLI

```bash
neuronx remember "I love pizza"
neuronx recall "What food?"
neuronx stats
neuronx audit
neuronx export json output.json
neuronx nrnlang 'FORGE engram("test")'
```

## REST API (curl)

```bash
# Remember
curl -X POST http://localhost:8000/api/v1/brain/remember \
  -H "Content-Type: application/json" \
  -d '{"text": "I love pizza"}'

# Recall
curl -X POST http://localhost:8000/api/v1/brain/recall \
  -H "Content-Type: application/json" \
  -d '{"query": "food", "top_k": 5}'

# Stats
curl http://localhost:8000/api/v1/brain/stats

# Export
curl http://localhost:8000/api/v1/export/json
```
