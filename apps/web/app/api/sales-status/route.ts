export const dynamic = "force-dynamic";

/**
 * 지금 값을 받을 수 있는가 — ★ 판정은 **결제 열쇠 하나**입니다.
 *
 * ★ 전에는 사업자 표시(`BIZ_READY`)가 여기서 한 번 더 막고 있었습니다.
 *   NEXT_PUBLIC_BIZ_* 여섯이 안 들어간 동안 `/v1/pay/config` 는
 *   enabled·live 둘 다 true 인데 화면은 결제 단추를 아예 안 그렸습니다 —
 *   라이브 키가 살아 있는데 한 사람도 못 사는 자리였습니다.
 *
 *   이제 **결제가 되느냐만** 봅니다. 사업자 표시는 `/legal` 이 맡습니다.
 *
 * ★ 시크릿 키는 이 라우트 밖으로 안 나갑니다. 내려보내는 것은
 *   「되는가 · 안 되면 왜」 둘뿐입니다.
 */
export async function GET() {
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
