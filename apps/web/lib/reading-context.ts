// In-memory only: navigation can keep a consultation, closing/reloading forgets it.
// Character-specific extras and birth data are never retained here.
let latest:{chart:string;concern:string;consultation:Record<string,unknown>}|null=null;
export function rememberReadingContext(chart:string,concern:string,answers:Record<string,string>){
  latest={chart,concern,consultation:{concern,answers:{...answers}}};
}
export function readingContext(chart:string|null,concern:string):Record<string,unknown>|null{
  return latest&&latest.chart===chart&&latest.concern===concern?{consultation:latest.consultation}:null;
}
