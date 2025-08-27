import { NextResponse } from "next/server";
import { Redis } from "@upstash/redis";
import { v4 as uuidv4 } from "uuid";

const redis = Redis.fromEnv();

export async function POST(req: Request) {
  try {
    const bouquet = await req.json();
    const id = uuidv4();
    // set with TTL 30 days (in seconds)
    await redis.set(`bouquet:${id}`, bouquet, { ex: 60 * 60 * 24 * 30 });
    return NextResponse.json({ id });
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 });
  }
}
