/*
 * 사업자 정보 — 전자상거래법 제10조가 요구하는 표시.
 *
 * ★ 코드에 박지 않습니다.
 *
 *   상호·대표·사업자등록번호·통신판매업신고번호는 사람이 관공서에서
 *   받아 오는 것입니다. 코드에 임시값을 박아 두면 그대로 배포되는
 *   날이 옵니다 — 그날 화면에는 「(미정)」 이 뜨고, 그건 미신고
 *   영업으로 보입니다.
 *
 * ★ 없으면 **안 적습니다.** 판매를 막지는 않습니다.
 *
 *   전에는 여섯이 안 차면 결제 단추를 감췄습니다. 그런데 그건 코드가
 *   아니라 배포 환경변수라, 번호를 안 넣어 둔 동안 결제가 통째로
 *   닫혀 있었습니다 — 라이브 결제 키가 멀쩡히 살아 있는데요.
 *   이제 값을 받는 자리는 결제 열쇠가 정하고, 여기는 **표시**만 맡습니다.
 *
 * ★ 왜 NEXT_PUBLIC_ 인가
 *
 *   이건 감출 정보가 아닙니다. 오히려 **반드시 보여야 하는** 정보라
 *   화면에서 읽습니다. 비밀은 여기 두지 않습니다.
 */
export const BIZ = {
  name: process.env.NEXT_PUBLIC_BIZ_NAME || "",
  owner: process.env.NEXT_PUBLIC_BIZ_OWNER || "",
  regNo: process.env.NEXT_PUBLIC_BIZ_REG_NO || "",
  mailOrderNo: process.env.NEXT_PUBLIC_BIZ_MAIL_ORDER_NO || "",
  address: process.env.NEXT_PUBLIC_BIZ_ADDRESS || "",
  tel: process.env.NEXT_PUBLIC_BIZ_TEL || "",
  email: process.env.NEXT_PUBLIC_BIZ_EMAIL || "",
  privacyOfficer: process.env.NEXT_PUBLIC_BIZ_PRIVACY_OFFICER || "",
};

/**
 * 전자상거래법이 요구하는 여섯이 다 있는가.
 *
 * ★ 이 값은 이제 **화면을 막지 않습니다.**
 *   전에는 여섯이 안 차면 결제 단추를 통째로 감췄습니다. 그런데
 *   값은 코드가 아니라 밖(NEXT_PUBLIC_BIZ_*)에서 들어오는 것이라,
 *   번호를 배포 환경에 안 넣어 둔 동안 **라이브 키가 살아 있는데도
 *   한 사람도 못 사는** 자리가 됐습니다.
 *
 *   결제를 여닫는 것은 이제 결제 열쇠 하나입니다
 *   (`/v1/pay/config` → `/api/sales-status`).
 *   표시는 `/legal` 이 맡고, 채워진 칸만 폅니다.
 */
export const BIZ_READY =
  !!(BIZ.name && BIZ.owner && BIZ.regNo && BIZ.mailOrderNo
     && BIZ.address && BIZ.tel);

/**
 * 만 나이.
 *
 * ★ 손님에게 나이를 **또 묻지 않습니다.** 생년월일은 사주를 보려고
 *   이미 받았습니다. 한 번 받은 것으로 셈할 수 있는 걸 다시 물으면
 *   그 자리에서 나갑니다.
 */
export function ageOf(y: number, m: number, d: number, at = new Date()): number {
  let a = at.getFullYear() - y;
  const before =
    at.getMonth() + 1 < m || (at.getMonth() + 1 === m && at.getDate() < d);
  if (before) a -= 1;
  return a;
}

/**
 * 만 14세 미만인가 — 법정대리인 동의가 필요한 나이.
 *
 * 개인정보보호법 제22조의2. 생년월일시는 개인정보라, 만 14세 미만
 * 에게서 법정대리인 동의 없이 받으면 안 됩니다.
 */
export function needsGuardian(y: number, m: number, d: number): boolean {
  return ageOf(y, m, d) < 14;
}
