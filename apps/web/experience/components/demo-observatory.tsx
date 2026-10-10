"use client";
import { demoSource } from "@/lib/demo/synthetic-source";
import { SubscriberPortfolioExperience } from "./subscriber-portfolio";
import { DemoNotice } from "./demo-notice";

/**
 * The subscriber's Observatory in its demonstration context: the same components, a fictional snapshot, no session
 * and no operations. It is always labelled as a demonstration. Nothing here reads private data or writes anything.
 */
export function DemoObservatory() {
  return <SubscriberPortfolioExperience source={demoSource} notice={<DemoNotice/>}/>;
}
