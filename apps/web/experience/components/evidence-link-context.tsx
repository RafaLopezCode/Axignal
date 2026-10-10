"use client";
/**
 * Demo mode uses exactly the same evidence presentation, but synthetic provenance
 * must never promise a navigable external document. Real subscriber/Staff links
 * remain governed by the existing URL validator.
 */
import { createContext, useContext, type ReactNode } from "react";
import { evidenceUrl } from "@/lib/subscriber-contracts";

const SyntheticEvidence = createContext(false);

export function SyntheticEvidenceProvider({ children }: { children: ReactNode }) {
  return <SyntheticEvidence.Provider value={true}>{children}</SyntheticEvidence.Provider>;
}

export function useEvidenceLink() {
  const synthetic = useContext(SyntheticEvidence);
  return {
    synthetic,
    href: (url: string | null | undefined) => synthetic ? null : evidenceUrl(url),
  };
}
