import { FramedObserver, type NarratorScene } from "./observer-frame";

/** Decorative narrator: adjacent canonical copy carries all product meaning. */
export function LandingGuide({
  scene,
  className = "",
}: {
  scene: NarratorScene;
  className?: string;
}) {
  return (
    <div className={"landing-guide " + className} aria-hidden="true">
      <FramedObserver scene={scene} />
    </div>
  );
}
