import { FramedObserver, type NarratorScene } from "./observer-frame";

/** Decorative narrator: adjacent canonical copy carries all product meaning. */
export function LandingGuide({
  scene,
  className = "",
  note,
}: {
  scene: NarratorScene;
  className?: string;
  note?: string;
}) {
  return (
    <div className={"landing-guide " + className} aria-hidden="true">
      <FramedObserver scene={scene} />
      {note && <span className="hand-note observer-guide-note">{note}</span>}
    </div>
  );
}
