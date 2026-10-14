/**
 * Reason formatting utilities for WardPulse.
 * Ensures clinical pattern lines (baseline deviations, condition boosts, drift)
 * are prominently displayed as the card's primary reason.
 */

export function extractPatternReason(reasonOrReasons?: string | string[]): string | null {
  if (!reasonOrReasons) return null;

  const lines = Array.isArray(reasonOrReasons)
    ? reasonOrReasons
    : reasonOrReasons.split(/\s*;\s*|\n+/);

  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const lower = trimmed.toLowerCase();

    // Check for explicit pattern keywords or clinical condition patterns
    if (
      lower.startsWith('pattern:') ||
      lower.includes('copd') ||
      lower.includes('post-op') ||
      lower.includes('cardiac') ||
      lower.includes('baseline') ||
      lower.includes('rising rapidly') ||
      lower.includes('falling vs baseline') ||
      lower.includes('elevated vs baseline') ||
      lower.includes('drift') ||
      lower.includes('shock index') ||
      lower.includes('hypoxia for')
    ) {
      return trimmed;
    }
  }

  return null;
}

export function formatCardReason(
  taskReason?: string,
  fallbackTitle?: string,
  assessmentReasons?: string[]
): string {
  // If assessment reasons contains a pattern line, prioritize it
  const fromAssessment = extractPatternReason(assessmentReasons);
  if (fromAssessment) {
    return fromAssessment;
  }

  // If task.reason contains a pattern line (or semicolon-separated parts), extract it
  const fromTask = extractPatternReason(taskReason);
  if (fromTask) {
    return fromTask;
  }

  return taskReason || fallbackTitle || '';
}
