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
 * ★ 없으면 **못 팝니다.**
 *
 *   결제 키가 없으면 결제를 거절하는 것과 같은 규칙입니다. 표시가
 *   빠진 채로 돈을 받는 것이 표시가 빠진 채로 무료로 보여 주는 것보다
 *   훨씬 위험합니다. `sellable` 이 그 자리를 지킵니다.
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

/** 전자상거래법이 요구하는 여섯이 다 있는가. */
export const BIZ_READY =
  !!(BIZ.name && BIZ.owner && BIZ.regNo && BIZ.mailOrderNo
     && BIZ.address && BIZ.tel);

/**
 * 팔아도 되는가.
 *
 * ★ 화면이 이걸 보고 결제 단추를 감춥니다. 무료 구간은 그대로
 *   보여 줍니다 — 표시 의무는 **판매**에 붙는 것이라, 안 파는
 *   동안에는 서비스를 닫을 이유가 없습니다.
 */
export const SELLABLE = BIZ_READY;

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
