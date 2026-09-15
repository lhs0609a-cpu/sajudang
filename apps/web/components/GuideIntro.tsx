import EntryGreeting from './EntryGreeting';

/** The guide is introduced before any character dialogue or personal input. */
export default function GuideIntro() {
  return <section className="guide-intro" aria-label="성신당 길잡이 소개">
    <EntryGreeting />
  </section>;
}
