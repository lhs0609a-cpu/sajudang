import profiles from './character-profiles.json';
type Concern = 'money' | 'work' | 'love' | 'people' | 'dir' | 'health';
export function characterConcerns(lensId: string): readonly string[] {
  return profiles[lensId as keyof typeof profiles]?.concerns ?? ['money','work','love','people','dir','health'];
}
export function characterConcern(lensId: string, concern: Concern): Concern {
  const profile = profiles[lensId as keyof typeof profiles];
  return profile && !profile.concerns.includes(concern) ? profile.default_concern as Concern : concern;
}
