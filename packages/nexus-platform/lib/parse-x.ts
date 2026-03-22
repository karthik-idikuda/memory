/**
 * PARSE-X — Intent Extraction Engine
 * Extracts technical specifications from vague user prompts
 */

export interface ParsedIntent {
  action: 'create' | 'modify' | 'debug' | 'deploy' | 'explain';
  framework: string;
  components: string[];
  styling: string;
  features: string[];
  ambiguityScore: number;
  clarifications: string[];
  nexlangTokens: string[];
}

const FRAMEWORK_PATTERNS: Record<string, RegExp> = {
  'react': /react|next\.?js|nextjs/i,
  'vue': /vue|nuxt/i,
  'svelte': /svelte/i,
  'angular': /angular/i,
  'html': /html|vanilla|plain|simple/i,
};

const ACTION_PATTERNS: Record<string, RegExp> = {
  'create': /build|create|make|generate|new|start/i,
  'modify': /change|update|modify|edit|fix|add|remove/i,
  'debug': /debug|fix|error|bug|broken|crash|issue/i,
  'deploy': /deploy|publish|ship|host|launch/i,
  'explain': /explain|how|what|why|show/i,
};

export function parseIntent(prompt: string): ParsedIntent {
  // Detect action
  let action: ParsedIntent['action'] = 'create';
  for (const [act, pattern] of Object.entries(ACTION_PATTERNS)) {
    if (pattern.test(prompt)) {
      action = act as ParsedIntent['action'];
      break;
    }
  }

  // Detect framework
  let framework = 'react';
  for (const [fw, pattern] of Object.entries(FRAMEWORK_PATTERNS)) {
    if (pattern.test(prompt)) {
      framework = fw;
      break;
    }
  }

  // Extract components
  const componentPatterns = /(?:button|form|modal|card|table|list|nav|header|footer|sidebar|menu|input|dropdown|carousel|chart|dashboard|login|signup|landing)/gi;
  const components = [...new Set((prompt.match(componentPatterns) || []).map(c => c.toLowerCase()))];

  // Extract features
  const featurePatterns = /(?:authentication|auth|api|database|search|filter|sort|pagination|dark mode|responsive|animation|drag.?drop|real.?time|upload|download|notification)/gi;
  const features = [...new Set((prompt.match(featurePatterns) || []).map(f => f.toLowerCase()))];

  // Detect styling
  let styling = 'tailwind';
  if (/css|vanilla css/i.test(prompt)) styling = 'css';
  if (/styled.?component/i.test(prompt)) styling = 'styled-components';
  if (/bootstrap/i.test(prompt)) styling = 'bootstrap';

  // Calculate ambiguity (0 = clear, 1 = very ambiguous)
  const wordCount = prompt.split(/\s+/).length;
  const specificity = components.length + features.length;
  const ambiguityScore = Math.max(0, Math.min(1, 1 - (specificity * 0.15) - (wordCount > 20 ? 0.2 : 0)));

  // Generate clarifications if ambiguous
  const clarifications: string[] = [];
  if (ambiguityScore > 0.6) {
    if (components.length === 0) clarifications.push('What specific components do you need?');
    if (features.length === 0) clarifications.push('Any specific features like auth, database, or API?');
    if (wordCount < 5) clarifications.push('Can you describe the project in more detail?');
  }

  // Generate NEXLANG-Ω tokens
  const nexlangTokens = [
    `[INTENT>>${action.toUpperCase()}]`,
    `[FRAME::${framework.toUpperCase()}]`,
    ...components.map(c => `[COMP::${c.toUpperCase()}]`),
    `[AMBIG::${(ambiguityScore * 100).toFixed(0)}]`,
  ];

  return {
    action,
    framework,
    components,
    styling,
    features,
    ambiguityScore,
    clarifications,
    nexlangTokens,
  };
}
