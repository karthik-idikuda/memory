/**
 * SECUREGEN-X — Security Scoring Engine
 * Scores generated code 0-100 for vulnerabilities
 */

export interface SecurityResult {
  score: number;
  grade: 'A' | 'B' | 'C' | 'D' | 'F';
  vulnerabilities: Vulnerability[];
  safe: boolean;
}

export interface Vulnerability {
  type: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  line: number;
  description: string;
  fix: string;
  penalty: number;
}

const RULES: Array<{
  pattern: RegExp;
  type: string;
  severity: Vulnerability['severity'];
  description: string;
  fix: string;
  penalty: number;
}> = [
  {
    pattern: /eval\s*\(/g,
    type: 'code-injection',
    severity: 'critical',
    description: 'eval() allows arbitrary code execution',
    fix: 'Use JSON.parse() or Function constructor with validation',
    penalty: 30,
  },
  {
    pattern: /innerHTML\s*=/g,
    type: 'xss',
    severity: 'high',
    description: 'innerHTML can lead to XSS attacks',
    fix: 'Use textContent or sanitize with DOMPurify',
    penalty: 15,
  },
  {
    pattern: /dangerouslySetInnerHTML/g,
    type: 'xss',
    severity: 'medium',
    description: 'dangerouslySetInnerHTML bypasses React XSS protection',
    fix: 'Use a sanitization library like DOMPurify',
    penalty: 10,
  },
  {
    pattern: /(?:api[_-]?key|secret|password|token)\s*[:=]\s*['"][^'"]+['"]/gi,
    type: 'credential-exposure',
    severity: 'critical',
    description: 'Hardcoded credentials detected',
    fix: 'Use environment variables (process.env)',
    penalty: 40,
  },
  {
    pattern: /document\.write/g,
    type: 'xss',
    severity: 'high',
    description: 'document.write can inject malicious content',
    fix: 'Use DOM manipulation methods',
    penalty: 15,
  },
  {
    pattern: /SELECT\s+\*?\s+FROM\s+.*?\+/gi,
    type: 'sql-injection',
    severity: 'critical',
    description: 'SQL query built with string concatenation',
    fix: 'Use parameterized queries or ORM',
    penalty: 35,
  },
  {
    pattern: /cors\(\s*\)/g,
    type: 'cors-misconfiguration',
    severity: 'medium',
    description: 'CORS allows all origins',
    fix: 'Specify allowed origins explicitly',
    penalty: 10,
  },
  {
    pattern: /Math\.random\(\)/g,
    type: 'weak-crypto',
    severity: 'low',
    description: 'Math.random() is not cryptographically secure',
    fix: 'Use crypto.getRandomValues() for security-sensitive operations',
    penalty: 5,
  },
  {
    pattern: /http:\/\/(?!localhost)/g,
    type: 'insecure-transport',
    severity: 'medium',
    description: 'Non-HTTPS URL detected',
    fix: 'Use HTTPS for all external requests',
    penalty: 8,
  },
  {
    pattern: /\.exec\s*\(/g,
    type: 'command-injection',
    severity: 'critical',
    description: 'Potential command injection via exec()',
    fix: 'Validate and sanitize all inputs before execution',
    penalty: 30,
  },
];

export function scoreCode(code: string): SecurityResult {
  const lines = code.split('\n');
  const vulnerabilities: Vulnerability[] = [];
  let totalPenalty = 0;

  for (const rule of RULES) {
    let match;
    while ((match = rule.pattern.exec(code)) !== null) {
      const lineNumber = code.substring(0, match.index).split('\n').length;
      vulnerabilities.push({
        type: rule.type,
        severity: rule.severity,
        line: lineNumber,
        description: rule.description,
        fix: rule.fix,
        penalty: rule.penalty,
      });
      totalPenalty += rule.penalty;
    }
    // Reset regex lastIndex
    rule.pattern.lastIndex = 0;
  }

  const score = Math.max(0, Math.min(100, 100 - totalPenalty));

  let grade: SecurityResult['grade'];
  if (score >= 90) grade = 'A';
  else if (score >= 80) grade = 'B';
  else if (score >= 70) grade = 'C';
  else if (score >= 60) grade = 'D';
  else grade = 'F';

  return {
    score,
    grade,
    vulnerabilities,
    safe: score >= 70,
  };
}
