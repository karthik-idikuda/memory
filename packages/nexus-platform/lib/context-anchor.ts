/**
 * CONTEXT-ANCHOR — Context Preservation Algorithm
 * Prevents quality degradation over long conversations
 * Checkpoints every N prompts, rebuilds context from anchors
 */

export interface ContextCheckpoint {
  id: string;
  timestamp: number;
  promptIndex: number;
  summary: string;
  codeSnapshot: string;
  fileStructure: string[];
  decisions: string[];
  qualityScore: number;
}

export interface AnchoredContext {
  checkpoints: ContextCheckpoint[];
  currentPromptIndex: number;
  degradationScore: number;
  lastAnchorIndex: number;
}

const CHECKPOINT_INTERVAL = 10;
const MAX_HISTORY = 20;

export function createContext(): AnchoredContext {
  return {
    checkpoints: [],
    currentPromptIndex: 0,
    degradationScore: 0,
    lastAnchorIndex: 0,
  };
}

export function shouldCheckpoint(ctx: AnchoredContext): boolean {
  return (ctx.currentPromptIndex - ctx.lastAnchorIndex) >= CHECKPOINT_INTERVAL;
}

export function addCheckpoint(
  ctx: AnchoredContext,
  summary: string,
  codeSnapshot: string,
  fileStructure: string[],
  decisions: string[]
): AnchoredContext {
  const checkpoint: ContextCheckpoint = {
    id: `anchor-${Date.now()}`,
    timestamp: Date.now(),
    promptIndex: ctx.currentPromptIndex,
    summary,
    codeSnapshot,
    fileStructure,
    decisions,
    qualityScore: 100 - ctx.degradationScore,
  };

  return {
    ...ctx,
    checkpoints: [...ctx.checkpoints, checkpoint],
    lastAnchorIndex: ctx.currentPromptIndex,
    degradationScore: 0,
  };
}

export function incrementPrompt(ctx: AnchoredContext): AnchoredContext {
  const newIndex = ctx.currentPromptIndex + 1;
  const promptsSinceAnchor = newIndex - ctx.lastAnchorIndex;

  // Degradation increases logarithmically
  const degradation = Math.min(50, Math.log2(promptsSinceAnchor + 1) * 8);

  return {
    ...ctx,
    currentPromptIndex: newIndex,
    degradationScore: degradation,
  };
}

export function rebuildContext(ctx: AnchoredContext): string {
  if (ctx.checkpoints.length === 0) return '';

  const recent = ctx.checkpoints.slice(-3);
  return recent.map(cp => (
    `[ANCHOR@${cp.promptIndex}] ${cp.summary}\n` +
    `Files: ${cp.fileStructure.join(', ')}\n` +
    `Decisions: ${cp.decisions.join('; ')}`
  )).join('\n\n');
}

export function trimHistory(
  messages: Array<{ role: string; content: string }>,
  ctx: AnchoredContext
): Array<{ role: string; content: string }> {
  if (messages.length <= MAX_HISTORY) return messages;

  const anchorSummary = rebuildContext(ctx);
  const trimmed = messages.slice(-MAX_HISTORY);

  if (anchorSummary) {
    trimmed.unshift({
      role: 'system',
      content: `[CONTEXT-ANCHOR] Previous context summary:\n${anchorSummary}`,
    });
  }

  return trimmed;
}
