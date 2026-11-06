# Simulation profile

Step = one simulation stage (generation, full/digitisation simulation,
digitisation, reconstruction of sim input), configured by options /
`DQ`-style parameter files and driver macros.

- The pipeline is defined by options files and driver scripts; the indexer
  must parse the options/parameter files, not only the drivers.
- Checks are physics-level distributions and detector response (yield ratios,
  resolution, efficiency vs kinematics) against a reference sim campaign on
  matched input, plus determinism: same seed + config hash => same output hash.
- Cross-check generator-level truth vs reconstruction-level outputs per step;
  record the campaign/geometry/tag in `state/log.jsonl`.
- Validate on a small fixed event count first; batch production jobs are
  submitted by the human, the agent only validates their outputs.
