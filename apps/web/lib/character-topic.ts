import profiles from './character-profiles.json';
type Concern = 'money' | 'work' | 'love' | 'people' | 'dir' | 'health' | 'real_estate';
export function characterConcerns(lensId: string): readonly string[] {
  const base = profiles[lensId as keyof typeof profiles]?.concerns ?? ['money','work','love','people','dir','health'];
  return base.includes('real_estate') ? base : [...base, 'real_estate'];
}
export function characterConcern(lensId: string, concern: Concern): Concern {
  if (concern === 'real_estate') return concern;
  const profile = profiles[lensId as keyof typeof profiles];
  return profile && !profile.concerns.includes(concern) ? profile.default_concern as Concern : concern;
}
