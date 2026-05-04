const PYTHON = "python";

const DEFAULTS = {
  profile: "DEFAULT",
  warehouseId: "585750a8283c627a",
  sqliteOut: "verification/runs/full_seed.sqlite",
  csvDir: "verification/exports/full_csv",
  schemaJsonDir: "verification/schema/full_json",
  manifest: "verification/exports/full_csv/generation_manifest.csv",
  workspacePrefix: "/Workspace/Shared/generated",
  notebooksOutDir: "workspace/notebooks/generated",
  taskId: "TASK-001-short-slug",
  taskFile: "tasks/TASK-001-short-slug.yaml",
  geniePromptOut: "verification/prompts/TASK-001-genie.md",
  genieResponseOut: "verification/responses/TASK-001-genie.json",
  workspaceMetadataSql: "eval/workspace_metadata/TASK-001-short-slug_metadata.sql",
  genieSpaceConfig: "workspace/genie/space_config.json",
  genieSpaceId: "<genie-space-id>",
  envFile: ".env",
};

const OPTIONS = {
  writeMode: ["replace", "append", "create-if-not-exists"],
  notebookMode: ["both", "anchors", "distractors"],
  codeMode: ["both", "sql", "python"],
  composition: ["separate", "same", "mixed"],
  surface: ["data", "notebooks"],
  ablation: ["on", "off"],
  dryRun: [
    { value: "", label: "Off" },
    { value: "--dry-run", label: "On (--dry-run)" },
  ],
  overwrite: [
    { value: "--overwrite", label: "On (--overwrite)" },
    { value: "", label: "Off" },
  ],
  minimalHint: [
    { value: "", label: "No minimal hint" },
    { value: "--include-minimal-hint", label: "Include minimal hint" },
  ],
  llmJudge: [
    { value: "", label: "Deterministic only" },
    { value: "--llm-sql-judge", label: "Add LLM SQL judge" },
  ],
  schemaComments: [
    { value: "", label: "Include schema comments" },
    { value: "--no-include-schema-comments", label: "Table/column comments only" },
  ],
  assetSelection: [
    { value: "all", label: "All asset tables" },
    { value: "selected", label: "Selected taxonomy IDs" },
    { value: "random", label: "Random taxonomy sample" },
  ],
  goldSource: [
    { value: "generate", label: "Generate gold now" },
    { value: "manifest", label: "Use existing gold CSV manifest" },
  ],
  assetsOnly: [
    { value: "", label: "Gold + asset tables" },
    { value: "--assets-only", label: "Asset tables only" },
  ],
  extraTables: [
    { value: "", label: "Fail extra tables" },
    { value: "--allow-extra-tables", label: "Allow extra tables" },
  ],
};

const GENERATE_DATA_OUTPUTS = {
  all: {
    sqliteOut: "verification/runs/full_seed.sqlite",
    csvDir: "verification/exports/full_csv",
    schemaJsonDir: "verification/schema/full_json",
  },
  selected: {
    sqliteOut: "verification/runs/selected_assets_seed.sqlite",
    csvDir: "verification/exports/selected_assets_csv",
    schemaJsonDir: "verification/schema/selected_assets_json",
  },
  random: {
    sqliteOut: "verification/runs/random_assets_seed.sqlite",
    csvDir: "verification/exports/random_assets_csv",
    schemaJsonDir: "verification/schema/random_assets_json",
  },
  manifest: {
    sqliteOut: "verification/runs/gold_plus_assets_from_manifest.sqlite",
    csvDir: "verification/exports/gold_plus_assets_from_manifest_csv",
    schemaJsonDir: "verification/schema/gold_plus_assets_from_manifest_json",
  },
  assetsOnly: {
    sqliteOut: "verification/runs/assets_only_seed.sqlite",
    csvDir: "verification/exports/assets_only_csv",
    schemaJsonDir: "verification/schema/assets_only_json",
  },
};

const HELP_CONTENT = {
  assetSelection: {
    title: "Asset selection",
    items: [
      ["All asset tables", "Generate every available table anchor/distractor type."],
      ["Selected taxonomy IDs", "Show ID fields and include only the anchor/distractor IDs you enter."],
      ["Random taxonomy sample", "Show count fields and sample that many anchor/distractor types using the seed."],
    ],
  },
  goldSource: {
    title: "Gold source",
    items: [
      ["Generate gold now", "Rebuild gold tables in this run, then generate assets from those tables."],
      ["Use existing gold CSV manifest", "Read an existing generation_manifest.csv and generate assets from that exact gold CSV state."],
    ],
  },
  assetsOnly: {
    title: "Output contents with existing gold",
    items: [
      ["Gold + asset tables", "Write the existing gold tables plus generated asset tables to the output."],
      ["Asset tables only", "Write only the generated anchor/distractor asset tables."],
    ],
  },
};

const TAXONOMY_REFERENCE = [
  {
    title: "Distractor table/schema IDs",
    items: [
      ["1.a.i", "worse catalog"],
      ["1.a.ii", "worse schema"],
      ["1.a.iii", "worse name or hash/materialization suffix"],
      ["1.a.iv", "no comment"],
      ["1.a.v", "deprecated or worse comment"],
      ["1.a.vi.a", "missing authoritative tag"],
      ["1.a.vi.b", "non-authoritative/deprecated tag"],
      ["1.a.vii", "wrong semantics"],
      ["1.a.viii", "rollup or pre-aggregated grain"],
    ],
  },
  {
    title: "Distractor notebook/dashboard IDs",
    items: [
      ["1.b.i", "notebook points to deprecated table"],
      ["1.b.ii", "notebook computes a similar but wrong metric"],
      ["1.b.iii", "buggy non-authoritative notebook"],
      ["1.c.i", "dashboard points to deprecated table"],
      ["1.c.ii", "dashboard computes a similar but wrong metric"],
      ["1.c.iii", "buggy non-authoritative dashboard"],
      ["2", "non-asset distractor signal"],
    ],
  },
  {
    title: "Anchor IDs",
    items: [
      ["1.a.i", "authoritative table"],
      ["1.a.ii", "non-authoritative comment but correct table"],
      ["1.a.iii", "non-authoritative catalog but correct table"],
      ["1.a.iv", "non-authoritative metadata but correct table"],
      ["1.b.i", "authoritative notebook reference"],
      ["1.b.ii", "non-authoritative notebook reference"],
      ["1.c.i", "authoritative dashboard"],
      ["1.c.ii", "non-authoritative dashboard"],
      ["1.d.i", "authoritative drive document"],
      ["1.d.ii", "non-authoritative drive document"],
      ["2.a.i", "column usage instruction"],
      ["2.a.ii", "column join-resolution hint"],
      ["2.b", "authoritative table tag"],
      ["2.c", "lineage signal"],
      ["2.d", "usage signal"],
      ["2.e", "freshness signal"],
    ],
  },
];

const SECTIONS = [
  {
    id: "deploy",
    label: "Deploy",
    description: "Push generated CSV data, notebooks, and workspace metadata into Databricks.",
    commands: [
      {
        id: "whoami",
        label: "Check Databricks connection",
        description: "Test Databricks SDK authentication through your configured profile/browser auth.",
        fields: [{ key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile }],
        build: (v) => `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} whoami`,
      },
      {
        id: "load-manifest",
        label: "Overwrite data from manifest",
        description: "Upload every CSV listed in generation_manifest.csv and write the target Delta tables.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "manifest", label: "CSV generation manifest", defaultValue: DEFAULTS.manifest },
          { key: "mode", label: "Write mode", defaultValue: "replace", options: OPTIONS.writeMode },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId },
          { key: "dryRun", label: "Dry run flag", defaultValue: "", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} load-manifest`,
          `--manifest ${quote(v.manifest)}`,
          `--mode ${v.mode || "replace"}`,
          v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "load-csv",
        label: "Upload one CSV",
        description: "Infer the target table for one CSV from the generation manifest.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "csvFile", label: "CSV file", defaultValue: "verification/exports/full_csv/certified/branches.csv" },
          { key: "manifest", label: "CSV generation manifest", defaultValue: DEFAULTS.manifest },
          { key: "mode", label: "Write mode", defaultValue: "replace", options: OPTIONS.writeMode },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId },
          { key: "dryRun", label: "Dry run flag", defaultValue: "", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} load-csv`,
          `--csv-file ${quote(v.csvFile)}`,
          `--manifest ${quote(v.manifest)}`,
          `--mode ${v.mode || "replace"}`,
          v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "drop-manifest",
        label: "Drop manifest tables",
        description: "Drop every Databricks table listed in the CSV generation manifest.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "manifest", label: "CSV generation manifest", defaultValue: DEFAULTS.manifest },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId },
          { key: "dryRun", label: "Dry run flag", defaultValue: "--dry-run", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} drop-manifest`,
          `--manifest ${quote(v.manifest)}`,
          v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "push-notebooks",
        label: "Overwrite notebooks",
        description: "Import notebook source files from one or more notebook manifests.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          {
            key: "notebookManifests",
            label: "Notebook manifests, one per line",
            defaultValue:
              "workspace/manifests/gold/notebooks.yaml\nworkspace/manifests/anchors/notebooks.yaml\nworkspace/manifests/distractor/notebooks.yaml",
            multiline: true,
          },
          { key: "overwrite", label: "Overwrite flag", defaultValue: "--overwrite", options: OPTIONS.overwrite },
          { key: "dryRun", label: "Dry run flag", defaultValue: "", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} push-notebooks`,
          ...lines(v.notebookManifests).map((manifest) => `--manifest ${quote(manifest)}`),
          v.overwrite ? "--overwrite" : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "apply-workspace-metadata",
        label: "Apply workspace metadata",
        description: "Run generated schema/table/column metadata SQL against Databricks.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "sqlFile", label: "Workspace metadata SQL file", defaultValue: DEFAULTS.workspaceMetadataSql },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId },
          { key: "dryRun", label: "Dry run flag", defaultValue: "--dry-run", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} run-sql-file`,
          `--sql-file ${quote(v.sqlFile || DEFAULTS.workspaceMetadataSql)}`,
          v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "list-genie-spaces",
        label: "List Genie Spaces",
        description: "List Genie Spaces visible to the current Databricks profile.",
        fields: [{ key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile }],
        build: (v) => `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} list-genie-spaces`,
      },
      {
        id: "create-genie-space",
        label: "Create Genie Space",
        description: "Create a Databricks Genie Space from a generated serialized-space config JSON.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "config", label: "Genie Space config JSON", defaultValue: DEFAULTS.genieSpaceConfig },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId },
          { key: "title", label: "Title override", defaultValue: "" },
          { key: "parentPath", label: "Parent workspace path", defaultValue: "/Workspace/Shared" },
          { key: "dryRun", label: "Dry run flag", defaultValue: "--dry-run", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} create-genie-space`,
          `--config ${quote(v.config || DEFAULTS.genieSpaceConfig)}`,
          v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.title ? `--title ${quote(v.title)}` : "",
          v.parentPath ? `--parent-path ${quote(v.parentPath)}` : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
    ],
  },
  {
    id: "generate",
    label: "Generate",
    description: "Create local gold data, generated anchor/distractor asset data, and notebook source files.",
    commands: [
      {
        id: "generate-data",
        label: "Generate gold + asset data",
        description: "Build gold tables plus generated table anchors and table distractors; choose all, selected IDs, or random sampling.",
        fields: [
          {
            key: "assetSelection",
            label: "Asset selection",
            defaultValue: "all",
            options: OPTIONS.assetSelection,
            affectsVisibility: true,
            affectsOutputDefaults: true,
            helpKey: "assetSelection",
          },
          {
            key: "goldSource",
            label: "Gold source",
            defaultValue: "generate",
            options: OPTIONS.goldSource,
            affectsVisibility: true,
            affectsOutputDefaults: true,
            helpKey: "goldSource",
          },
          {
            key: "goldManifest",
            label: "Existing gold CSV manifest",
            defaultValue: "verification/exports/gold_csv/generation_manifest.csv",
            showWhen: (v) => v.goldSource === "manifest",
          },
          {
            key: "assetsOnly",
            label: "Output contents with existing gold",
            defaultValue: "",
            options: OPTIONS.assetsOnly,
            showWhen: (v) => v.goldSource === "manifest",
            affectsOutputDefaults: true,
            helpKey: "assetsOnly",
          },
          {
            key: "anchorTypes",
            label: "Anchor taxonomy IDs",
            defaultValue: "1.a.i,2.a.ii",
            taxonomyReference: true,
            showWhen: (v) => v.assetSelection === "selected",
          },
          {
            key: "distractorTypes",
            label: "Distractor taxonomy IDs",
            defaultValue: "1.a.i,1.a.viii",
            taxonomyReference: true,
            showWhen: (v) => v.assetSelection === "selected",
          },
          {
            key: "randomAnchors",
            label: "Random anchor count",
            defaultValue: "2",
            showWhen: (v) => v.assetSelection === "random",
          },
          {
            key: "randomDistractors",
            label: "Random distractor count",
            defaultValue: "3",
            showWhen: (v) => v.assetSelection === "random",
          },
          { key: "sqliteOut", label: "SQLite output", defaultValue: DEFAULTS.sqliteOut },
          { key: "csvDir", label: "CSV output directory", defaultValue: DEFAULTS.csvDir },
          { key: "schemaJsonDir", label: "JSON schema directory", defaultValue: DEFAULTS.schemaJsonDir },
          { key: "seed", label: "Seed", defaultValue: "42" },
          { key: "scale", label: "Scale", defaultValue: "1.0" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.generators.run`,
          "--target sqlite",
          v.goldSource === "manifest" ? `--gold-manifest ${quote(v.goldManifest)}` : "",
          v.goldSource === "manifest" && v.assetsOnly ? "--assets-only" : "",
          v.assetSelection === "selected" ? `--anchor-types ${v.anchorTypes || "1.a.i,2.a.ii"}` : "",
          v.assetSelection === "selected" ? `--distractor-types ${v.distractorTypes || "1.a.i,1.a.viii"}` : "",
          v.assetSelection === "random" ? `--random-anchors ${v.randomAnchors || "2"}` : "",
          v.assetSelection === "random" ? `--random-distractors ${v.randomDistractors || "3"}` : "",
          `--out ${quote(v.sqliteOut)}`,
          `--csv-dir ${quote(v.csvDir)}`,
          `--schema-json-dir ${quote(v.schemaJsonDir)}`,
          `--seed ${v.seed || "42"}`,
          `--scale ${v.scale || "1.0"}`,
        ]),
      },
      {
        id: "generate-gold-data",
        label: "Generate gold-only data",
        description: "Build only the gold workspace tables without generated anchor/distractor asset tables.",
        fields: [
          { key: "sqliteOut", label: "SQLite output", defaultValue: "verification/runs/gold_seed.sqlite" },
          { key: "csvDir", label: "CSV output directory", defaultValue: "verification/exports/gold_csv" },
          { key: "schemaJsonDir", label: "JSON schema directory", defaultValue: "verification/schema/gold_json" },
          { key: "seed", label: "Seed", defaultValue: "42" },
          { key: "scale", label: "Scale", defaultValue: "1.0" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.generators.run`,
          "--target sqlite",
          "--gold-only",
          `--out ${quote(v.sqliteOut)}`,
          `--csv-dir ${quote(v.csvDir)}`,
          `--schema-json-dir ${quote(v.schemaJsonDir)}`,
          `--seed ${v.seed || "42"}`,
          `--scale ${v.scale || "1.0"}`,
        ]),
      },
      {
        id: "generate-notebooks",
        label: "Generate notebooks from static specs",
        description: "Create notebook assets from built-in specs and update notebook manifests. This does not call the LLM.",
        fields: [
          { key: "mode", label: "Mode", defaultValue: "both", options: OPTIONS.notebookMode },
          { key: "ids", label: "Notebook taxonomy IDs", defaultValue: "1.b.i,1.b.iii", taxonomyReference: true },
          { key: "codeMode", label: "Code mode", defaultValue: "both", options: OPTIONS.codeMode },
          { key: "composition", label: "Composition", defaultValue: "separate", options: OPTIONS.composition },
          { key: "outDir", label: "Notebook output directory", defaultValue: DEFAULTS.notebooksOutDir },
          { key: "workspacePrefix", label: "Workspace prefix", defaultValue: DEFAULTS.workspacePrefix },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.generators.generate_notebooks`,
          `--mode ${v.mode || "both"}`,
          v.ids ? `--ids ${v.ids}` : "--all",
          `--code-mode ${v.codeMode || "both"}`,
          `--composition ${v.composition || "separate"}`,
          `--out-dir ${quote(v.outDir)}`,
          `--workspace-prefix ${quote(v.workspacePrefix)}`,
        ]),
      },
      {
        id: "generate-llm-notebooks",
        label: "Generate notebooks with LLM specs",
        description: "Ask the LLM for notebook specs, then write notebook files and manifests.",
        fields: [
          { key: "anchorCount", label: "Anchor notebook count", defaultValue: "2" },
          { key: "distractorCount", label: "Distractor notebook count", defaultValue: "4" },
          { key: "envFile", label: "Env file", defaultValue: DEFAULTS.envFile },
          { key: "specOut", label: "Generated spec JSON", defaultValue: "workspace/generators/notebook_specs/generated_notebook_specs.json" },
          { key: "codeMode", label: "Code mode", defaultValue: "both", options: OPTIONS.codeMode },
          { key: "composition", label: "Composition", defaultValue: "separate", options: OPTIONS.composition },
          { key: "outDir", label: "Notebook output directory", defaultValue: DEFAULTS.notebooksOutDir },
          { key: "workspacePrefix", label: "Workspace prefix", defaultValue: DEFAULTS.workspacePrefix },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.generators.generate_notebooks`,
          "--mode both",
          `--anchor-count ${v.anchorCount || "2"}`,
          `--distractor-count ${v.distractorCount || "4"}`,
          "--spec-source llm",
          `--spec-out ${quote(v.specOut)}`,
          `--env-file ${quote(v.envFile)}`,
          `--code-mode ${v.codeMode || "both"}`,
          `--composition ${v.composition || "separate"}`,
          `--out-dir ${quote(v.outDir)}`,
          `--workspace-prefix ${quote(v.workspacePrefix)}`,
        ]),
      },
    ],
  },
  {
    id: "genie",
    label: "Task Authoring",
    description: "Create task templates and build the Genie prompt that should be sent to Databricks Genie.",
    commands: [
      {
        id: "create-task",
        label: "Create task template",
        description: "Create a new task YAML from tasks/_template.yaml and fill the basic fields.",
        fields: [
          { key: "taskId", label: "Task ID / filename stem", defaultValue: DEFAULTS.taskId },
          { key: "title", label: "Title", defaultValue: "Human-readable title" },
          { key: "question", label: "Question", defaultValue: "TBD - the natural-language question the agent receives.", multiline: true },
          { key: "tasksDir", label: "Tasks directory", defaultValue: "tasks" },
          { key: "overwrite", label: "Overwrite flag", defaultValue: "", options: OPTIONS.overwrite },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/create_task.py`,
          `--task-id ${quote(v.taskId || DEFAULTS.taskId)}`,
          v.title ? `--title ${quote(v.title)}` : "",
          v.question ? `--question ${quote(v.question)}` : "",
          `--tasks-dir ${quote(v.tasksDir || "tasks")}`,
          v.overwrite ? "--overwrite" : "",
        ]),
      },
      {
        id: "genie-prompt",
        label: "Build Genie prompt",
        description: "Build the safe Genie prompt from a task YAML: question plus eval JSON contract only.",
        fields: [
          { key: "taskFile", label: "Task YAML", defaultValue: DEFAULTS.taskFile },
          { key: "minimalHint", label: "Minimal hint", defaultValue: "", options: OPTIONS.minimalHint },
          { key: "out", label: "Output markdown path", defaultValue: DEFAULTS.geniePromptOut },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/genie_prompt_builder.py ${quote(v.taskFile)}`,
          v.minimalHint ? "--include-minimal-hint" : "",
          v.out ? `--out ${quote(v.out)}` : "",
        ]),
      },
      {
        id: "build-workspace-metadata",
        label: "Build workspace metadata SQL",
        description: "Create neutral Unity Catalog comments from task-declared informative and distracting table/column metadata.",
        fields: [
          { key: "taskFile", label: "Task YAML", defaultValue: DEFAULTS.taskFile },
          { key: "out", label: "Output SQL file", defaultValue: DEFAULTS.workspaceMetadataSql },
          { key: "schemaComments", label: "Schema comments", defaultValue: "", options: OPTIONS.schemaComments },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/build_workspace_metadata_sql.py`,
          `--task ${quote(v.taskFile)}`,
          `--out ${quote(v.out || DEFAULTS.workspaceMetadataSql)}`,
          v.schemaComments ? "--no-include-schema-comments" : "",
        ]),
      },
      {
        id: "build-genie-space-config",
        label: "Build Genie Space config",
        description: "Create a serialized Genie Space config from local schema metadata and task questions/gold SQL.",
        fields: [
          { key: "schemaDir", label: "JSON schema directory", defaultValue: DEFAULTS.schemaJsonDir },
          { key: "taskFile", label: "Task YAML", defaultValue: DEFAULTS.taskFile },
          { key: "out", label: "Output config JSON", defaultValue: DEFAULTS.genieSpaceConfig },
          { key: "title", label: "Space title", defaultValue: "duck-rl-gym Genie Space" },
          { key: "warehouseId", label: "SQL warehouse ID placeholder", defaultValue: DEFAULTS.warehouseId },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/build_genie_space_config.py`,
          `--schema-dir ${quote(v.schemaDir || DEFAULTS.schemaJsonDir)}`,
          `--task ${quote(v.taskFile || DEFAULTS.taskFile)}`,
          `--out ${quote(v.out || DEFAULTS.genieSpaceConfig)}`,
          v.title ? `--title ${quote(v.title)}` : "",
          v.warehouseId ? `--warehouse-id ${quote(v.warehouseId)}` : "",
        ]),
      },
    ],
  },
  {
    id: "tasks",
    label: "Task Verification",
    description: "Validate task YAML, build coverage, and check saved Genie responses against canonical answers.",
    commands: [
      {
        id: "validate-tasks",
        label: "Validate task specs",
        description: "Run the task spec validator.",
        fields: [{ key: "tasksDir", label: "Tasks directory", defaultValue: "tasks" }],
        build: (v) => `${PYTHON} tools/validate_task_specs.py --tasks-dir ${quote(v.tasksDir)}`,
      },
      {
        id: "coverage",
        label: "Build coverage matrix",
        description: "Create taxonomy coverage markdown from task declarations.",
        fields: [
          { key: "tasksDir", label: "Tasks directory", defaultValue: "tasks" },
          { key: "coverageOut", label: "Coverage output", defaultValue: "verification/coverage.md" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/coverage_matrix.py`,
          `--tasks-dir ${quote(v.tasksDir)}`,
          `--out ${quote(v.coverageOut)}`,
        ]),
      },
      {
        id: "verify-genie-response",
        label: "Verify Genie response",
        description: "Check Genie SQL output, reported result rows, and semantic SQL/assets against a task YAML.",
        fields: [
          { key: "taskFile", label: "Task YAML", defaultValue: DEFAULTS.taskFile },
          { key: "responseFile", label: "Saved Genie response", defaultValue: DEFAULTS.genieResponseOut },
          { key: "dbPath", label: "SQLite DB path", defaultValue: DEFAULTS.sqliteOut },
          { key: "out", label: "Harness report output", defaultValue: "verification/runs/TASK-001-harness.json" },
          { key: "llmSqlJudge", label: "LLM SQL judge", defaultValue: "", options: OPTIONS.llmJudge },
          { key: "llmModel", label: "LLM judge model", defaultValue: "gpt-4.1-mini" },
          { key: "envFile", label: "Env file", defaultValue: DEFAULTS.envFile },
          { key: "allowExtraTables", label: "Extra tables", defaultValue: "", options: OPTIONS.extraTables },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m harness.runner`,
          `--task ${quote(v.taskFile)}`,
          `--response ${quote(v.responseFile)}`,
          `--db ${quote(v.dbPath)}`,
          v.out ? `--out ${quote(v.out)}` : "",
          v.allowExtraTables ? "--allow-extra-tables" : "",
          v.llmSqlJudge ? "--llm-sql-judge" : "",
          v.llmSqlJudge && v.llmModel ? `--llm-model ${quote(v.llmModel)}` : "",
          v.llmSqlJudge && v.envFile ? `--env-file ${quote(v.envFile)}` : "",
        ]),
      },
      {
        id: "ask-genie",
        label: "Ask Genie with prompt",
        description: "Start a Genie conversation using a generated prompt file so the response can be saved and verified.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "spaceId", label: "Genie Space ID", defaultValue: DEFAULTS.genieSpaceId },
          { key: "promptFile", label: "Prompt file", defaultValue: DEFAULTS.geniePromptOut },
          { key: "out", label: "Save response JSON", defaultValue: DEFAULTS.genieResponseOut },
          { key: "dryRun", label: "Dry run flag", defaultValue: "--dry-run", options: OPTIONS.dryRun },
        ],
        build: (v) => appendRedirect(
          joinCommand([
            `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} ask-genie`,
            `--space-id ${quote(v.spaceId || DEFAULTS.genieSpaceId)}`,
            `--prompt-file ${quote(v.promptFile || DEFAULTS.geniePromptOut)}`,
            v.dryRun ? "--dry-run" : "",
          ]),
          v.dryRun ? "" : v.out
        ),
      },
    ],
  },
  {
    id: "prompts",
    label: "Tools",
    description: "General repo utilities: prompt builders, local SQLite inspection, and table-name mapping helpers.",
    commands: [
      {
        id: "anchor-distractor-prompt",
        label: "Build anchor/distractor prompt",
        description: "Create a markdown prompt for data or notebook surface generation.",
        fields: [
          { key: "surface", label: "Surface", defaultValue: "data", options: OPTIONS.surface },
          { key: "mode", label: "Mode", defaultValue: "both", options: OPTIONS.notebookMode },
          { key: "ids", label: "Taxonomy IDs", defaultValue: "1.a.i,2.a.ii", taxonomyReference: true },
          { key: "domain", label: "Domain focus", defaultValue: "" },
          { key: "out", label: "Prompt output path", defaultValue: "workspace/generators/prompts/custom_anchor_distractor_prompt.md" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.generators.anchor_distractor_prompt`,
          `--surface ${v.surface || "data"}`,
          `--mode ${v.mode || "both"}`,
          `--ids ${v.ids || "1.a.i,2.a.ii"}`,
          v.domain ? `--domain ${quote(v.domain)}` : "",
          `--out ${quote(v.out)}`,
        ]),
      },
      {
        id: "sqlite-query",
        label: "Run local SQL",
        description: "Run SQL against SQLite while allowing canonical Databricks table names.",
        fields: [
          { key: "dbPath", label: "SQLite DB path", defaultValue: DEFAULTS.sqliteOut },
          {
            key: "sql",
            label: "SQL",
            defaultValue:
              "select branch_id, sum(fee_amount_usd) as total_fee from main.finance_core.fee_revenue group by 1 order by 2 desc limit 5",
            multiline: true,
          },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/sqlite_query.py`,
          `--db ${quote(v.dbPath)}`,
          `--sql ${quote(v.sql)}`,
          "--show-sql",
        ]),
      },
      {
        id: "sqlite-mapping",
        label: "List SQLite mapping",
        description: "Show how Databricks 3-part table names map to local SQLite table names.",
        fields: [{ key: "dbPath", label: "SQLite DB path", defaultValue: DEFAULTS.sqliteOut }],
        build: (v) => `${PYTHON} tools/sqlite_query.py --db ${quote(v.dbPath)} --list-mapping`,
      },
    ],
  },
];

let activeSection = SECTIONS[0];
let activeCommand = activeSection.commands[0];
let values = {};

document.addEventListener("DOMContentLoaded", () => {
  renderTabs();
  renderTaxonomyReference();
  setSection(SECTIONS[0].id);
  document.getElementById("command-select").addEventListener("change", (event) => {
    setCommand(event.target.value);
  });
  document.getElementById("copy-command").addEventListener("click", copyCommand);
  document.getElementById("taxonomy-close").addEventListener("click", closeTaxonomyModal);
  document.getElementById("help-close").addEventListener("click", closeHelpModal);
  document.getElementById("taxonomy-modal").addEventListener("click", (event) => {
    if (event.target.id === "taxonomy-modal") closeTaxonomyModal();
  });
  document.getElementById("help-modal").addEventListener("click", (event) => {
    if (event.target.id === "help-modal") closeHelpModal();
  });
});

function renderTabs() {
  const tabs = document.getElementById("databricks-tabs");
  tabs.innerHTML = SECTIONS.map(
    (section) => `<button type="button" class="tab-button" data-section="${section.id}">${section.label}</button>`
  ).join("");
  tabs.querySelectorAll(".tab-button").forEach((button) => {
    button.addEventListener("click", () => setSection(button.dataset.section));
  });
}

function setSection(sectionId) {
  activeSection = SECTIONS.find((section) => section.id === sectionId) || SECTIONS[0];
  document.querySelectorAll(".tab-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.section === activeSection.id);
  });
  document.getElementById("section-description").textContent = activeSection.description || "";
  const select = document.getElementById("command-select");
  select.innerHTML = activeSection.commands.map(
    (command) => `<option value="${escapeHtml(command.id)}">${escapeHtml(command.label)}</option>`
  ).join("");
  setCommand(activeSection.commands[0].id);
}

function setCommand(commandId) {
  activeCommand = activeSection.commands.find((command) => command.id === commandId) || activeSection.commands[0];
  values = {};
  activeCommand.fields.forEach((field) => {
    values[field.key] = field.defaultValue || "";
  });
  document.getElementById("command-select").value = activeCommand.id;
  document.getElementById("command-description").textContent = activeCommand.description;
  renderFields();
  updateOutput();
}

function renderFields() {
  const container = document.getElementById("command-fields");
  const fields = visibleFields(activeCommand, values);
  container.innerHTML = fields.map((field) => renderField(field)).join("");
  fields.forEach((field) => {
    const input = document.getElementById(`field-${field.key}`);
    input.addEventListener("input", (event) => {
      values[field.key] = event.target.value;
      if (activeCommand.id === "generate-data" && field.affectsOutputDefaults) {
        Object.assign(values, generateDataOutputDefaults(values));
      }
      if (field.affectsVisibility) renderFields();
      updateOutput();
    });
    input.addEventListener("change", (event) => {
      values[field.key] = event.target.value;
      if (activeCommand.id === "generate-data" && field.affectsOutputDefaults) {
        Object.assign(values, generateDataOutputDefaults(values));
      }
      if (field.affectsVisibility) renderFields();
      updateOutput();
    });
  });
}

function visibleFields(command, currentValues) {
  return command.fields.filter((field) => !field.showWhen || field.showWhen(currentValues));
}

function generateDataOutputDefaults(currentValues) {
  if (currentValues.goldSource === "manifest" && currentValues.assetsOnly) {
    return GENERATE_DATA_OUTPUTS.assetsOnly;
  }
  if (currentValues.goldSource === "manifest") {
    return GENERATE_DATA_OUTPUTS.manifest;
  }
  return GENERATE_DATA_OUTPUTS[currentValues.assetSelection || "all"] || GENERATE_DATA_OUTPUTS.all;
}

function renderField(field) {
  const inputId = `field-${field.key}`;
  const currentValue = values[field.key] ?? field.defaultValue ?? "";
  const helpButton = field.helpKey
    ? `<button type="button" class="help-button" data-help-key="${escapeHtml(field.helpKey)}" aria-label="Explain ${escapeHtml(field.label)}">?</button>`
    : "";
  const label = field.taxonomyReference
    ? `<div class="field-label-row"><label class="field-label" for="${inputId}">${escapeHtml(field.label)}</label><button type="button" class="taxonomy-button" data-taxonomy-open="true">View IDs</button></div>`
    : `<div class="field-label-row"><label class="field-label" for="${inputId}">${escapeHtml(field.label)}</label>${helpButton}</div>`;
  if (field.options) {
    const options = field.options.map((option) => {
      const value = typeof option === "string" ? option : option.value;
      const text = typeof option === "string" ? option : option.label;
      const selected = value === currentValue ? "selected" : "";
      return `<option value="${escapeHtml(value)}" ${selected}>${escapeHtml(text)}</option>`;
    }).join("");
    return `<div>${label}<select id="${inputId}" class="command-control">${options}</select></div>`;
  }
  if (field.multiline) {
    return `<div>${label}<textarea id="${inputId}" class="command-textarea">${escapeHtml(currentValue)}</textarea></div>`;
  }
  return `<div>${label}<input id="${inputId}" class="command-control" value="${escapeHtml(currentValue)}"></div>`;
}

function renderTaxonomyReference() {
  const container = document.getElementById("taxonomy-reference");
  container.innerHTML = TAXONOMY_REFERENCE.map((section) => `
    <section class="taxonomy-section">
      <h3>${escapeHtml(section.title)}</h3>
      ${section.items.map(([id, description]) => `
        <div class="taxonomy-row">
          <span class="taxonomy-id">${escapeHtml(id)}</span>
          <span class="taxonomy-description">${escapeHtml(description)}</span>
        </div>
      `).join("")}
    </section>
  `).join("");
}

document.addEventListener("click", (event) => {
  if (event.target.matches("[data-taxonomy-open='true']")) {
    openTaxonomyModal();
  }
  if (event.target.matches("[data-help-key]")) {
    openHelpModal(event.target.dataset.helpKey);
  }
});

function openTaxonomyModal() {
  const modal = document.getElementById("taxonomy-modal");
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function closeTaxonomyModal() {
  const modal = document.getElementById("taxonomy-modal");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

function openHelpModal(helpKey) {
  const content = HELP_CONTENT[helpKey];
  if (!content) return;

  document.getElementById("help-title").textContent = content.title;
  document.getElementById("help-content").innerHTML = content.items.map(([title, body]) => `
    <section class="help-section">
      <h3>${escapeHtml(title)}</h3>
      <p>${escapeHtml(body)}</p>
    </section>
  `).join("");

  const modal = document.getElementById("help-modal");
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
}

function closeHelpModal() {
  const modal = document.getElementById("help-modal");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

function updateOutput() {
  document.getElementById("command-output").textContent = activeCommand.build(values);
}

async function copyCommand() {
  const command = document.getElementById("command-output").textContent;
  await navigator.clipboard.writeText(command);
  const button = document.getElementById("copy-command");
  button.textContent = "Copied";
  setTimeout(() => {
    button.textContent = "Copy";
  }, 1400);
}

function quote(value) {
  const text = String(value || "").trim();
  if (!text) return '""';
  if (/^[A-Za-z0-9_./:=,@+-]+$/.test(text)) return text;
  return `"${text.replace(/(["\\$`])/g, "\\$1")}"`;
}

function joinCommand(parts) {
  return parts.filter(Boolean).map((part, index) => (index === 0 ? part : `  ${part}`)).join(" \\\n");
}

function appendRedirect(command, outputPath) {
  return outputPath ? `${command} \\\n  > ${quote(outputPath)}` : command;
}

function lines(value) {
  return String(value || "").split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
