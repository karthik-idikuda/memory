/**
 * NEXLANG-Ω — Custom Notation Language for AI Operations
 * Token format: [CATEGORY::VALUE] or [CATEGORY>>VALUE]
 */

export interface NexlangToken {
  raw: string;
  category: string;
  operator: '::' | '>>';
  value: string;
}

const TOKEN_REGEX = /\[(\w+)(::?|>>)(\w+(?:[.\-/]\w+)*)\]/g;

export function parseTokens(input: string): NexlangToken[] {
  const tokens: NexlangToken[] = [];
  let match;

  while ((match = TOKEN_REGEX.exec(input)) !== null) {
    tokens.push({
      raw: match[0],
      category: match[1],
      operator: match[2] as '::' | '>>',
      value: match[3],
    });
  }

  TOKEN_REGEX.lastIndex = 0;
  return tokens;
}

export function generateTokens(data: {
  intent?: string;
  framework?: string;
  security?: number;
  agent?: string;
  memory?: string;
  context?: number;
}): string {
  const tokens: string[] = [];

  if (data.intent) tokens.push(`[INTENT>>${data.intent.toUpperCase()}]`);
  if (data.framework) tokens.push(`[FRAME::${data.framework.toUpperCase()}]`);
  if (data.security !== undefined) tokens.push(`[SCORE::SEC${data.security}]`);
  if (data.agent) tokens.push(`[AGENT>>${data.agent.toUpperCase()}]`);
  if (data.memory) tokens.push(`[MEM::${data.memory.toUpperCase()}]`);
  if (data.context !== undefined) tokens.push(`[CTX::ANCHOR${data.context}]`);

  return tokens.join(' ');
}

// Pre-defined symbol table
export const NEXLANG_SYMBOLS: Record<string, string> = {
  'INTENT>>': 'User intent classification',
  'FRAME::': 'Target framework',
  'SCORE::SEC': 'Security score',
  'SCORE::QUAL': 'Quality score',
  'AGENT>>': 'Active agent',
  'MEM::': 'Memory operation',
  'CTX::ANCHOR': 'Context anchor point',
  'FORGE::CODE': 'Code generation complete',
  'TRACE::ROOT': 'Root cause identified',
  'DEPLOY>>': 'Deployment target',
  'AMBIG::': 'Ambiguity percentage',
  'COMP::': 'Component type',
};
