import { NextRequest, NextResponse } from 'next/server';

const GROQ_API = 'https://api.groq.com/openai/v1/chat/completions';
const GROQ_KEY = process.env.GROQ_API_KEY || '';
const GROQ_MODEL = process.env.GROQ_MODEL || 'llama-3.3-70b-versatile';

const SYSTEM_PROMPT = `You are NEXUS-Ω, a multi-agentic AI coding platform. You have 6 specialized agents:
1. PARSE Agent — understands user intent precisely
2. ARCHITECT Agent — designs system architecture
3. CODEGEN Agent — writes production-grade code
4. SECURITY Agent — checks for vulnerabilities
5. DEBUG Agent — finds root causes of bugs
6. DEPLOY Agent — handles deployment

Core brain systems:
- NEURON-X: Persistent memory across sessions
- SIGMA-X: Causal reasoning and predictions
- CORTEX-X: Metacognitive self-monitoring

RULES:
- Always generate COMPLETE, RUNNABLE code — never partial
- Wrap code in proper markdown code blocks with language tags
- For web apps: generate complete HTML files with inline CSS and JS
- Use modern, clean, beautiful design — dark themes, smooth animations
- If generating React: include all imports and full component
- Be concise in explanations — code speaks louder than words
- Every response should include working code
- If asked to build something, provide a COMPLETE working implementation`;

export async function POST(req: NextRequest) {
  try {
    const { message, history, mode } = await req.json();

    if (!GROQ_KEY) {
      return NextResponse.json({
        content: '⚠️ Groq API key not configured. Go to **Settings** and add your Groq API key.',
        securityScore: 0,
      });
    }

    const messages: Array<{ role: string; content: string }> = [
      { role: 'system', content: SYSTEM_PROMPT },
    ];

    if (history && Array.isArray(history)) {
      for (const msg of history.slice(-10)) {
        messages.push({ role: msg.role === 'user' ? 'user' : 'assistant', content: msg.content });
      }
    }

    messages.push({ role: 'user', content: message });

    const startTime = Date.now();

    const res = await fetch(GROQ_API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GROQ_KEY}`,
      },
      body: JSON.stringify({
        model: GROQ_MODEL,
        messages,
        temperature: 0.7,
        max_tokens: 4096,
        stream: false,
      }),
    });

    const elapsed = Date.now() - startTime;

    if (!res.ok) {
      const err = await res.text();
      console.error('Groq error:', err);
      return NextResponse.json({
        content: `API Error (${res.status}). Check your Groq API key.`,
        securityScore: 0,
      });
    }

    const data = await res.json();
    const content = data.choices?.[0]?.message?.content || 'No response generated.';
    const tokens = data.usage?.total_tokens || 0;

    // Basic security scoring on generated code
    let securityScore = 94;
    if (content.includes('eval(')) securityScore -= 30;
    if (content.includes('innerHTML')) securityScore -= 10;
    if (content.includes('dangerouslySetInnerHTML')) securityScore -= 5;
    if (/sk[-_]|api[-_]key\s*[:=]/i.test(content)) securityScore -= 40;
    securityScore = Math.max(0, Math.min(100, securityScore));

    return NextResponse.json({
      content,
      securityScore,
      tokens,
      elapsed,
      model: GROQ_MODEL,
    });
  } catch (err) {
    console.error('Generate error:', err);
    return NextResponse.json({
      content: 'Server error. Please try again.',
      securityScore: 0,
    }, { status: 500 });
  }
}
