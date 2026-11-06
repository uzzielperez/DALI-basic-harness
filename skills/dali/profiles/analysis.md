# Analysis profile

Step = one analysis stage (selection, background estimate, efficiency, fit,
systematics), configured by the analysis code and its config files.

- The pipeline is defined by the analysis scripts and `state/pipeline.yaml`;
  each step has one Snakefile rule.
- Checks are scalars and distributions against the reference (paper /
  previous AN value): deviation in sigma for yields and efficiencies,
  chi2/KS for shapes, plus determinism on fixed input.
- Every reference number carries provenance (document, section/table);
  inferred values are marked `needs_review`.
- Validate on a small fixed sample first; full-stat runs need human approval.
