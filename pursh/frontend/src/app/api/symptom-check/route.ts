import { NextRequest, NextResponse } from "next/server";

const SYSTEM_PROMPT = `You are a medical triage assistant helping patients find the right specialist.
Ask ONE short follow-up question at a time with 4–5 answer options. Always include "None of these" as the last option.
After 2–4 exchanges, when you have enough information, respond with a result.

You MUST respond ONLY with valid JSON. No explanations. No text outside JSON.

Two response formats:

Question:
{"type":"question","question":"Short question here?","options":["Option A","Option B","Option C","Option D","None of these"]}

Result (when specialist is clear):
{"type":"result","specialty":"Dermatology","urgency":"routine"}

Valid specialties: General Practice, Dermatology, Mental Health, Hair & Scalp, Sexual Health, General Wellness, Weight Management
Valid urgency values: routine, urgent, emergency

If urgency is emergency, set specialty to "Emergency Care".`;

export type AIMessage = { role: "user" | "assistant"; content: string };

export interface SymptomCheckRequest {
  messages: AIMessage[];
}

export interface QuestionResponse {
  type: "question";
  question: string;
  options: string[];
}

export interface ResultResponse {
  type: "result";
  specialty: string;
  urgency: "routine" | "urgent" | "emergency";
}

export type SymptomCheckResponse = QuestionResponse | ResultResponse | { type: "error"; message: string };

export async function POST(req: NextRequest): Promise<NextResponse<SymptomCheckResponse>> {
  const apiKey = process.env.DEEPSEEK_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ type: "error", message: "AI service not configured." }, { status: 500 });
  }

  const body = (await req.json()) as SymptomCheckRequest;
  const { messages } = body;

  if (!messages?.length) {
    return NextResponse.json({ type: "error", message: "No messages provided." }, { status: 400 });
  }

  try {
    const res = await fetch("https://api.deepseek.com/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "deepseek-chat",
        messages: [{ role: "system", content: SYSTEM_PROMPT }, ...messages],
        temperature: 0.3,
        max_tokens: 300,
        response_format: { type: "json_object" },
      }),
      signal: AbortSignal.timeout(15000),
    });

    if (!res.ok) {
      const err = await res.text();
      console.error("DeepSeek error:", err);
      return NextResponse.json({ type: "error", message: "AI service unavailable." }, { status: 502 });
    }

    const data = await res.json();
    const raw = data?.choices?.[0]?.message?.content ?? "{}";
    const parsed = JSON.parse(raw) as SymptomCheckResponse;

    return NextResponse.json(parsed);
  } catch (e) {
    console.error("symptom-check error:", e);
    return NextResponse.json({ type: "error", message: "Could not reach AI service." }, { status: 502 });
  }
}
