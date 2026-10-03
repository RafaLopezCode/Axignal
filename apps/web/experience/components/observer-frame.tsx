"use client";
import { useId } from "react";

type CasePose = "guiding" | "analyzing" | "connecting" | "pointing" | "reflecting" | "accompanying";
// Same approved source sheet, same source-pixel scale and common ground line.
// Masks exclude the surrounding editorial notes, never redraw the character.
const frames: Record<CasePose, { centre: number; ground: number; mask: string }> = {
  guiding: { centre: 969, ground: 878, mask: "847,652 987,652 987,726 1089,726 1089,884 847,884" },
  analyzing: { centre: 444, ground: 878, mask: "429,684 481,684 512,704 518,725 518,884 356,884 356,777 367,756 374,727 400,707 423,696" },
  connecting: { centre: 699, ground: 878, mask: "589,649 799,649 799,884 589,884" },
  pointing: { centre: 714, ground: 1252, mask: "588,1048 725,1048 725,1110 738,1105 838,1090 838,1260 588,1260" },
  reflecting: { centre: 181, ground: 1252, mask: "132,1046 260,1046 260,1260 104,1260 104,1246 124,1246 124,1137 122,1129 116,1115 116,1084" },
  accompanying: { centre: 427, ground: 1252, mask: "306,1059 430,1059 430,1143 468,1143 468,1100 548,1100 548,1260 306,1260" },
};
export function FramedObserver({ pose, className = "" }: { pose: CasePose; className?: string }) {
  const clipId = "case-observer-" + useId().replaceAll(":", "");
  const frame = frames[pose];
  return (
    <svg className={"observer " + className} viewBox="0 0 290 260" role="img"
      aria-label="El Observador AXIGNAL" data-pose={pose}>
      <defs><clipPath id={clipId}><polygon points={frame.mask} /></clipPath></defs>
      <g transform={`translate(${145 - frame.centre} ${240 - frame.ground})`}>
        <image href="/observer/actions.png" width="1122" height="1402" clipPath={`url(#${clipId})`} />
      </g>
    </svg>
  );
}