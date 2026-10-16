import delivery from "./marketing-delivery.json";

const sourceSet = (name: keyof typeof delivery.images) =>
  delivery.images[name].variants.map(({url, width}) => `${url} ${width}w`).join(", ");

export const HERO_SRC_SET = sourceSet("hero-art");
// Below1280px the existing full plate is cropped by height; account for its full rendered width.
export const HERO_SIZES = "(max-width: 760px) 620px, (max-width: 1116px) 102vw, (max-width: 1279px) 1140px, 100vw";
export const INDUSTRY_SRC_SET = sourceSet("industries");
export const INDUSTRY_SIZES = "(max-width: 760px) calc(100vw - 44px), 90vw";
export const PUBLIC_BODY_FONT = delivery.fonts[0].url;
export const PUBLIC_DISPLAY_FONT = "/fonts/font-01.woff2";
