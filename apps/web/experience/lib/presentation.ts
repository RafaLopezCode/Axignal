/** MASTER §27 reference economics. This function never bills or grants access. */
export function monthlyReferenceCents(focuses: number): number {
  if (!Number.isSafeInteger(focuses) || focuses < 1 || focuses > 100)
    throw new RangeError(
      "Reference focus count must be an integer from 1 to 100.",
    );
  return 995 + 495 * (focuses - 1);
}
