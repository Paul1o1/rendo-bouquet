import { NextResponse } from "next/server";
import { kv } from "@vercel/kv";
import { v4 as uuidv4 } from "uuid";

export async function POST(req: Request) {
  try {
    const bouquet = await req.json();
    const id = uuidv4();
    await kv.set(`bouquet:${id}`, bouquet, { ex: 60 * 60 * 24 * 30 });
    return NextResponse.json({ id });
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }
}
