import { NextResponse } from "next/server";
import { kv } from "@vercel/kv";

export async function GET(
  _req: Request,
  { params }: { params: { id: string } }
) {
  const data = await kv.get(`bouquet:${params.id}`);
  if (!data) return NextResponse.json({ error: "Not found" }, { status: 404 });
  return NextResponse.json(data);
}
