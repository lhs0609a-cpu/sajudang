"use client";

/**
 * 토스페이먼츠 결제창.
 *
 * ★ 예전에는 window.prompt 로 paymentKey 를 사람에게 물어봤습니다.
 *   그건 붙다 만 자리표시였습니다. 실제 결제는 이렇게 돕니다.
 *
 *     ① 서버가 주문을 만든다        POST /v1/pay/prepare  → order_id · amount
 *     ② 토스 SDK 가 결제창을 띄운다  requestPayment(...)
 *     ③ 토스가 successUrl 로 되돌린다  ?paymentKey=…&orderId=…&amount=…
 *     ④ 서버가 승인한다              POST /v1/pay/confirm
 *
 * ★ 금액은 서버가 정합니다.
 *   여기서 넘기는 amount 는 화면에 띄우는 용도이고, 승인할 때는 서버가
 *   주문에 적어 둔 값을 씁니다. 여기 값을 고쳐도 싸게 못 삽니다.
 *
 * ★ 키가 없으면 결제창을 안 띄웁니다.
 *   성공한 척하지 않습니다. 화면이 "아직 값을 받을 수 없소" 를 냅니다.
 */

const SDK_SRC = "https://js.tosspayments.com/v2/standard";

/* 토스 SDK 는 타입 선언을 안 싣습니다. 쓰는 만큼만 좁게 적습니다. */
interface TossPaymentRequest {
  method: "CARD";
  amount: { currency: "KRW"; value: number };
  orderId: string;
  orderName: string;
  successUrl: string;
  failUrl: string;
  card?: { flowMode?: string; useEscrow?: boolean; useCardPoint?: boolean };
}
interface TossPayment {
  requestPayment(req: TossPaymentRequest): Promise<void>;
}
interface TossSdk {
  payment(opts: { customerKey: string }): TossPayment;
}
type TossFactory = (clientKey: string) => TossSdk;

declare global {
  interface Window {
    TossPayments?: TossFactory;
  }
}

let loading: Promise<TossFactory> | null = null;

/** SDK 를 한 번만 받아 둡니다. 결제 화면에 올 때만 부릅니다. */
export function loadToss(): Promise<TossFactory> {
  if (typeof window === "undefined") {
    return Promise.reject(new Error("브라우저에서만 됩니다."));
  }
  if (window.TossPayments) return Promise.resolve(window.TossPayments);
  if (loading) return loading;

  loading = new Promise<TossFactory>((resolve, reject) => {
    const el = document.createElement("script");
    el.src = SDK_SRC;
    el.async = true;
    el.onload = () => {
      if (window.TossPayments) resolve(window.TossPayments);
      else reject(new Error("결제 모듈을 읽지 못했소."));
    };
    el.onerror = () => {
      loading = null;               // 다음에 다시 시도할 수 있게
      reject(new Error("결제 모듈을 불러오지 못했소. 잠시 뒤 다시 해 보시오."));
    };
    document.head.appendChild(el);
  });
  return loading;
}

/**
 * 토스가 사람을 다시 데려올 주소.
 *
 * 결제창은 페이지를 통째로 떠났다가 돌아옵니다. 그래서 order_id 를
 * 주소에 실어 보냅니다 — 돌아왔을 때 어떤 주문이었는지 알아야 합니다.
 */
export function returnUrls(orderId: string) {
  const base = window.location.origin + "/pay";
  return {
    successUrl: `${base}?step=d2&toss=ok&order=${encodeURIComponent(orderId)}`,
    failUrl: `${base}?step=d2&toss=fail&order=${encodeURIComponent(orderId)}`,
  };
}

export async function openCheckout(opts: {
  clientKey: string;
  orderId: string;
  amount: number;
  orderName: string;
  /** 익명 열쇠. 생년월일·이름을 넣지 마세요 — PG 로 넘어갑니다. */
  customerKey: string;
}): Promise<void> {
  const TossPayments = await loadToss();
  const { successUrl, failUrl } = returnUrls(opts.orderId);
  await TossPayments(opts.clientKey)
    .payment({ customerKey: opts.customerKey })
    .requestPayment({
      method: "CARD",
      amount: { currency: "KRW", value: opts.amount },
      orderId: opts.orderId,
      orderName: opts.orderName,
      successUrl,
      failUrl,
      card: { flowMode: "DEFAULT", useEscrow: false, useCardPoint: false },
    });
}
