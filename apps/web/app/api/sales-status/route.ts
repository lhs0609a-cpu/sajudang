import { BIZ_READY } from "@/lib/biz";

export const dynamic = "force-dynamic";

/** One public readiness result. Provider credentials never leave this route. */
export async function GET() {
  if (!BIZ_READY) return Response.json({ready:false, reason:"seller_setup"});
  try {
    const base = process.env.API_BASE || process.env.NEXT_PUBLIC_API_BASE;
    if (!base) return Response.json({ready:false, reason:"gateway_setup"});
    const response = await fetch(`${base}/v1/pay/config`, {cache:"no-store", signal:AbortSignal.timeout(5000)});
    if (!response.ok) throw new Error("configuration unavailable");
    const config = await response.json();
    return Response.json({ready:config.enabled === true, reason:config.enabled ? null : "gateway_setup"});
  } catch {
    return Response.json({ready:false, reason:"temporary"});
  }
}
