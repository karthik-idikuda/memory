/**
 * TRACE-X — Causal Debug Engine
 * Finds root causes, builds causal chains, suggests fixes
 */

export interface TraceResult {
  rootCause: string;
  confidence: number;
  causalChain: CausalStep[];
  suggestedFix: string;
  pattern: string;
  preventionTip: string;
}

export interface CausalStep {
  order: number;
  description: string;
  type: 'trigger' | 'propagation' | 'failure';
}

const ERROR_PATTERNS: Array<{
  pattern: RegExp;
  rootCause: string;
  chain: string[];
  fix: string;
  prevention: string;
}> = [
  {
    pattern: /TypeError:\s*Cannot read propert(?:y|ies) of (undefined|null)/i,
    rootCause: 'Accessing property on null/undefined value',
    chain: ['Variable not initialized or API returned null', 'Property access attempted without null check', 'TypeError thrown at runtime'],
    fix: 'Add optional chaining (?.) or null check before access',
    prevention: 'Always use optional chaining for potentially null values',
  },
  {
    pattern: /ReferenceError:\s*(\w+) is not defined/i,
    rootCause: 'Variable or function used before declaration',
    chain: ['Variable/import missing from scope', 'Runtime cannot resolve reference', 'ReferenceError thrown'],
    fix: 'Import or declare the missing variable',
    prevention: 'Use TypeScript strict mode to catch undeclared variables',
  },
  {
    pattern: /SyntaxError/i,
    rootCause: 'Invalid syntax in source code',
    chain: ['Parser encountered unexpected token', 'Could not build AST', 'SyntaxError thrown before execution'],
    fix: 'Check for missing brackets, parentheses, or commas',
    prevention: 'Use a linter (ESLint) and format-on-save',
  },
  {
    pattern: /Maximum call stack|Maximum update depth/i,
    rootCause: 'Infinite recursion or render loop',
    chain: ['Function calls itself without base case', 'Call stack grows beyond limit', 'Stack overflow error'],
    fix: 'Add a base case to recursion or fix useEffect dependencies',
    prevention: 'Always define exit conditions for recursive functions',
  },
  {
    pattern: /CORS|Access-Control-Allow-Origin/i,
    rootCause: 'Cross-Origin Resource Sharing policy blocking request',
    chain: ['Browser sends preflight OPTIONS request', 'Server missing CORS headers', 'Browser blocks response'],
    fix: 'Configure server CORS headers to allow your origin',
    prevention: 'Set up CORS middleware in your API server',
  },
  {
    pattern: /Failed to fetch|NetworkError|ERR_CONNECTION/i,
    rootCause: 'Network request failed',
    chain: ['Client initiates HTTP request', 'DNS/network/server unreachable', 'Fetch promise rejects'],
    fix: 'Check if the server is running and URL is correct',
    prevention: 'Add error handling and retry logic for network requests',
  },
  {
    pattern: /Hydration|Text content does not match/i,
    rootCause: 'Server/client HTML mismatch (hydration error)',
    chain: ['Server renders initial HTML', 'Client renders different HTML', 'React detects mismatch'],
    fix: 'Ensure server and client render identical output; use useEffect for client-only code',
    prevention: 'Avoid window/document in render; use dynamic imports with ssr: false',
  },
];

export function analyzeError(errorMessage: string, code?: string): TraceResult {
  for (const ep of ERROR_PATTERNS) {
    if (ep.pattern.test(errorMessage)) {
      return {
        rootCause: ep.rootCause,
        confidence: 0.92,
        causalChain: ep.chain.map((desc, i) => ({
          order: i + 1,
          description: desc,
          type: i === 0 ? 'trigger' : i === ep.chain.length - 1 ? 'failure' : 'propagation',
        })),
        suggestedFix: ep.fix,
        pattern: ep.pattern.source,
        preventionTip: ep.prevention,
      };
    }
  }

  // Generic fallback
  return {
    rootCause: 'Unknown error pattern — requires AI analysis',
    confidence: 0.5,
    causalChain: [
      { order: 1, description: 'Error triggered', type: 'trigger' },
      { order: 2, description: errorMessage.slice(0, 100), type: 'failure' },
    ],
    suggestedFix: 'Send to AI debug agent for deeper analysis',
    pattern: 'unknown',
    preventionTip: 'Add comprehensive error handling and logging',
  };
}
