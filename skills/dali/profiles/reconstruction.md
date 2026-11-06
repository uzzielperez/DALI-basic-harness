# Reconstruction profile

Step = one algorithm or sequence stage (preprocessing/presel, graph
construction, model inference, matching, evaluation), configured by options or
YAML config files.

- The pipeline is defined in configs (`configs/`, YAML) and driver scripts,
  not only in a main script. The indexer must parse configs and algorithm
  sequences.
- Checks are distributions and performance curves (energy resolution,
  efficiency vs E/eta, fake/purity rates) against a reference reconstruction
  run on the same input, plus determinism: same input + config + seed => same
  output hash.
- Run everything on a small fixed input (few events) first. Full-scale jobs go
  through the batch system; the agent only checks their outputs.
- Pin and record the random seed and the full config hash in state/log.jsonl.
