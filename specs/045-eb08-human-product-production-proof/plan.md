# EB-08 implementation plan

1. Add a subscriber-runtime adapter over the existing EconomicHumanOutput.
2. Validate the resulting POTENTIAL/UNKNOWN Xignal with the existing TypeScript RuntimeProjection schema and first-map reader.
3. Add a FirstProofStore load/backup/recovery harness for 1/2/100 isolated contexts.
4. Run Python and frontend deterministic validation.
5. Build a controlled local runtime/browser product proof using the exact candidate code.
6. Integrate only after browser proof; deploy production only after integrated external E2E succeeds.
