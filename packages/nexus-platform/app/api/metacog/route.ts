import { NextResponse } from 'next/server';

export async function GET() {
  return NextResponse.json({
    clarity: 0,
    confidence: 0,
    creativity: 0,
    coherence: 0,
    overall: 0,
  });
}
