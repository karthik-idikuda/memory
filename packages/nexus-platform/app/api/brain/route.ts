import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // In production, this would connect to the actual NEURON-X backend
    // For now, return empty state (no fake data)
    return NextResponse.json({
      memories: [],
      stats: { total: 0, byType: {}, avgConfidence: 0 },
    });
  } catch {
    return NextResponse.json({ memories: [], stats: { total: 0, byType: {}, avgConfidence: 0 } });
  }
}
