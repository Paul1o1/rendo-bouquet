import { NextResponse } from "next/server";
import { Redis } from "@upstash/redis";

const redis = Redis.fromEnv();

export async function GET(
  _req: Request,
  { params }: { params: { id: string } }
) {
  const data = await redis.get(`bouquet:${params.id}`);
  if (!data) return NextResponse.json({ error: "Not found" }, { status: 404 });
  return NextResponse.json(data);
}
