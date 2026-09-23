import { CONCERNS, type Concern } from "@/lib/store";

/** Labels live in HTML so these illustrations never carry essential text. */
export function ConcernArtwork({ concern }: { concern: Concern }) {
  const asset = concern === 'real_estate' ? 'money' : concern;
  return <img src={`/images/concerns/${asset}-v2.webp`} alt="" width={480} height={480} decoding="async" />;
}

export function ConcernReminder({ concern }: { concern: Concern }) {
  const choice = CONCERNS.find((item) => item.id === concern)!;
  return <div className="concern-reminder">
    <ConcernArtwork concern={concern} />
    <div><small>함께 살펴볼 고민</small><p><b>{choice.label}</b><span>{choice.sub}</span></p></div>
  </div>;
}
