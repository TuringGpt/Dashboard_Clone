const PYTHON = "python";

const DEFAULTS = {
  environment: "meridian_mid_sized_bank",
  profile: "DEFAULT",
  warehouseId: "585750a8283c627a",
  sqliteOut: "workspace/meridian_mid_sized_bank/generated_data/runs/full_seed.sqlite",
  csvDir: "workspace/meridian_mid_sized_bank/generated_data/exports/full_csv",
  schemaJsonDir: "workspace/meridian_mid_sized_bank/generated_data/schema/full_json",
  manifest: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/gold/data/generation_manifest.csv",
  anchorDataManifest: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/anchors/assets/data/generation_manifest.csv",
  distractorDataManifest: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/distractors/assets/data/generation_manifest.csv",
  workspacePrefix: "/Workspace/Shared/utilities",
  notebooksOutDir: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/distractors/assets/notebooks",
  taskId: "TASK-001-top-fee-revenue-branch",
  taskBundle: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch",
  taskFile: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/task.yaml",
  anchorNotebookManifest: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/anchors/assets/notebooks/notebooks.yaml",
  distractorNotebookManifest: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/distractors/assets/notebooks/notebooks.yaml",
  geniePromptOut: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/genie_prompts/TASK-001-top-fee-revenue-branch-genie.md",
  genieResponseOut: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/genie_responses/TASK-001-top-fee-revenue-branch-genie.json",
  harnessOut: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/reports/harness/TASK-001-top-fee-revenue-branch-harness.json",
  workspaceMetadataSql: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/anchors/non_assets/scripts/apply_comments.sql",
  genieSpaceConfig: "workspace/meridian_mid_sized_bank/generated_data/genie/TASK-001_gold_fqns_space_config.json",
  genieSpaceId: "<genie-space-id>",
  envFile: ".env",
};

const OPTIONS = {
  writeMode: ["replace", "append", "create-if-not-exists"],
  notebookMode: ["both", "anchors", "distractors"],
  codeMode: ["both", "sql", "python"],
  composition: ["separate", "same", "mixed"],
  variant: ["gold", "anchors", "distractors", "full"],
  executor: ["databricks", "sqlite"],
  notebookAssetMode: ["distractors", "anchors", "both"],
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
  extraTables: [
    { value: "", label: "Fail extra tables" },
    { value: "--allow-extra-tables", label: "Allow extra tables" },
  ],
  deleteStaging: [
    { value: "", label: "Keep staging files" },
    { value: "--delete-staging", label: "Delete staging files" },
  ],
  specSource: ["static", "file", "api"],
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
    id: "data",
    label: "Gold Data",
    description: "Generate the shared Meridian gold dataset and build task-local bundles from it.",
    commands: [
      {
        id: "generate-gold-data",
        label: "Generate shared gold data",
        description: "Run the Meridian domain generator. It writes only trusted gold data into workspace/meridian_mid_sized_bank/generated_data/.",
        fields: [
          { key: "sqliteOut", label: "SQLite output", defaultValue: DEFAULTS.sqliteOut },
          { key: "csvDir", label: "CSV output directory", defaultValue: DEFAULTS.csvDir },
          { key: "schemaJsonDir", label: "JSON schema directory", defaultValue: DEFAULTS.schemaJsonDir },
          { key: "seed", label: "Seed", defaultValue: "42" },
          { key: "scale", label: "Scale", defaultValue: "1.0" },
          { key: "usersPool", label: "Optional users_pool.json", defaultValue: "" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.${DEFAULTS.environment}.generators.run`,
          `--out ${quote(v.sqliteOut || DEFAULTS.sqliteOut)}`,
          `--csv-dir ${quote(v.csvDir || DEFAULTS.csvDir)}`,
          `--schema-json-dir ${quote(v.schemaJsonDir || DEFAULTS.schemaJsonDir)}`,
          `--seed ${v.seed || "42"}`,
          `--scale ${v.scale || "1.0"}`,
          v.usersPool ? `--users-pool ${quote(v.usersPool)}` : "",
        ]),
      },
      {
        id: "build-all-bundles",
        label: "Build all task bundles",
        description: "Copy common gold artifacts into every task folder and refresh task-local scripts/manifests.",
        fields: [
          { key: "environment", label: "Environment", defaultValue: DEFAULTS.environment },
          { key: "tasksDir", label: "Tasks directory", defaultValue: "tasks" },
          { key: "overwrite", label: "Overwrite flag", defaultValue: "--overwrite", options: OPTIONS.overwrite },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/task_bundle.py build`,
          "--all",
          `--environment ${quote(v.environment || DEFAULTS.environment)}`,
          `--tasks-dir ${quote(v.tasksDir || "tasks")}`,
          v.overwrite ? "--overwrite" : "",
        ]),
      },
      {
        id: "build-one-bundle",
        label: "Build one task bundle",
        description: "Refresh a single task-local bundle from common generated gold artifacts.",
        fields: [
          { key: "taskFile", label: "Task YAML", defaultValue: DEFAULTS.taskFile },
          { key: "environment", label: "Environment", defaultValue: DEFAULTS.environment },
          { key: "overwrite", label: "Overwrite flag", defaultValue: "--overwrite", options: OPTIONS.overwrite },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/task_bundle.py build`,
          `--task ${quote(v.taskFile || DEFAULTS.taskFile)}`,
          `--environment ${quote(v.environment || DEFAULTS.environment)}`,
          v.overwrite ? "--overwrite" : "",
        ]),
      },
    ],
  },
  {
    id: "task-assets",
    label: "Task Assets",
    description: "Load, apply, ablate, or remove the task-local gold, anchor, and distractor assets.",
    commands: [
      {
        id: "load-task-gold",
        label: "Load task gold",
        description: "Load only the task's canonical gold tables into Databricks.",
        fields: [{ key: "taskBundle", label: "Task folder", defaultValue: DEFAULTS.taskBundle }],
        build: (v) => `bash ${quote(pathJoin(v.taskBundle || DEFAULTS.taskBundle, "scripts/load_gold.sh"))}`,
      },
      {
        id: "apply-anchors",
        label: "Apply anchors",
        description: "Apply task-local anchor assets and non-asset anchor scripts.",
        fields: [{ key: "taskBundle", label: "Task folder", defaultValue: DEFAULTS.taskBundle }],
        build: (v) => `bash ${quote(pathJoin(v.taskBundle || DEFAULTS.taskBundle, "scripts/apply_anchors.sh"))}`,
      },
      {
        id: "apply-distractors",
        label: "Apply distractors",
        description: "Apply task-local distractor assets and non-asset distractor scripts.",
        fields: [{ key: "taskBundle", label: "Task folder", defaultValue: DEFAULTS.taskBundle }],
        build: (v) => `bash ${quote(pathJoin(v.taskBundle || DEFAULTS.taskBundle, "scripts/apply_distractors.sh"))}`,
      },
      {
        id: "load-full-task",
        label: "Load full task",
        description: "Load gold, anchors, and distractors for a task.",
        fields: [{ key: "taskBundle", label: "Task folder", defaultValue: DEFAULTS.taskBundle }],
        build: (v) => `bash ${quote(pathJoin(v.taskBundle || DEFAULTS.taskBundle, "scripts/load_full.sh"))}`,
      },
      {
        id: "ablate-anchors",
        label: "Ablate anchors",
        description: "Remove or revert task-local anchors while leaving the task otherwise usable.",
        fields: [{ key: "taskBundle", label: "Task folder", defaultValue: DEFAULTS.taskBundle }],
        build: (v) => `bash ${quote(pathJoin(v.taskBundle || DEFAULTS.taskBundle, "scripts/ablate_anchors.sh"))}`,
      },
      {
        id: "ablate-distractors",
        label: "Ablate distractors",
        description: "Remove or revert task-local distractors for the ablated arm of a check.",
        fields: [{ key: "taskBundle", label: "Task folder", defaultValue: DEFAULTS.taskBundle }],
        build: (v) => `bash ${quote(pathJoin(v.taskBundle || DEFAULTS.taskBundle, "scripts/ablate_distractors.sh"))}`,
      },
      {
        id: "revert-full-script",
        label: "Revert full task script",
        description: "Run the task-local revert script generated with the bundle.",
        fields: [{ key: "taskBundle", label: "Task folder", defaultValue: DEFAULTS.taskBundle }],
        build: (v) => `bash ${quote(pathJoin(v.taskBundle || DEFAULTS.taskBundle, "scripts/revert_full.sh"))}`,
      },
      {
        id: "revert-task-variant",
        label: "Revert task variant",
        description: "Use the bundler revert command to drop gold, anchors, distractors, or everything for a task.",
        fields: [
          { key: "taskBundle", label: "Task folder", defaultValue: DEFAULTS.taskBundle },
          { key: "variant", label: "Variant", defaultValue: "full", options: OPTIONS.variant },
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId },
          { key: "deleteStaging", label: "Staging cleanup", defaultValue: "", options: OPTIONS.deleteStaging },
          { key: "dryRun", label: "Dry run flag", defaultValue: "--dry-run", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/task_bundle.py revert`,
          `--bundle ${quote(v.taskBundle || DEFAULTS.taskBundle)}`,
          `--variant ${v.variant || "full"}`,
          v.profile ? `--profile ${v.profile}` : "",
          v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.deleteStaging ? "--delete-staging" : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
    ],
  },
  {
    id: "databricks",
    label: "Databricks Push",
    description: "Create workspace folders, push task-local notebooks, load manifests, and run task-local SQL scripts.",
    commands: [
      {
        id: "whoami",
        label: "Check Databricks connection",
        description: "Test Databricks SDK authentication through your configured profile/browser auth.",
        fields: [{ key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile }],
        build: (v) => `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} whoami`,
      },
      {
        id: "create-workspace-dir",
        label: "Create workspace folder",
        description: "Create a task or utility folder in Databricks Workspace without uploading assets.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "workspacePath", label: "Workspace path", defaultValue: "/Workspace/Shared/utilities" },
          { key: "subdirs", label: "Subdirectories, one per line", defaultValue: "", multiline: true },
          { key: "dryRun", label: "Dry run flag", defaultValue: "--dry-run", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} create-workspace-dir`,
          `--workspace-path ${quote(v.workspacePath || "/Workspace/Shared/utilities")}`,
          ...lines(v.subdirs).map((subdir) => `--subdir ${quote(subdir)}`),
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "push-task-notebooks",
        label: "Push task notebooks",
        description: "Import task-local anchor and/or distractor notebooks. Manifest workspace paths are used as-is.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "mode", label: "Notebook set", defaultValue: "distractors", options: OPTIONS.notebookAssetMode, affectsVisibility: true },
          { key: "anchorManifest", label: "Anchor notebook manifest", defaultValue: DEFAULTS.anchorNotebookManifest, showWhen: (v) => v.mode === "anchors" || v.mode === "both" },
          { key: "distractorManifest", label: "Distractor notebook manifest", defaultValue: DEFAULTS.distractorNotebookManifest, showWhen: (v) => v.mode === "distractors" || v.mode === "both" },
          { key: "overwrite", label: "Overwrite flag", defaultValue: "--overwrite", options: OPTIONS.overwrite },
          { key: "dryRun", label: "Dry run flag", defaultValue: "", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} push-notebooks`,
          ...(v.mode === "anchors" || v.mode === "both" ? [`--manifest ${quote(v.anchorManifest || DEFAULTS.anchorNotebookManifest)}`] : []),
          ...(v.mode === "distractors" || v.mode === "both" ? [`--manifest ${quote(v.distractorManifest || DEFAULTS.distractorNotebookManifest)}`] : []),
          v.overwrite ? "--overwrite" : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "load-manifest",
        label: "Load manifest tables",
        description: "Upload every CSV listed in a task-local generation_manifest.csv and write the target Delta tables.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "manifest", label: "CSV generation manifest", defaultValue: DEFAULTS.manifest },
          { key: "mode", label: "Write mode", defaultValue: "replace", options: OPTIONS.writeMode },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId },
          { key: "dryRun", label: "Dry run flag", defaultValue: "", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} load-manifest`,
          `--manifest ${quote(v.manifest || DEFAULTS.manifest)}`,
          `--mode ${v.mode || "replace"}`,
          v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "drop-manifest",
        label: "Drop manifest tables",
        description: "Drop every Databricks table listed in a task-local generation_manifest.csv.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "manifest", label: "CSV generation manifest", defaultValue: DEFAULTS.manifest },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId },
          { key: "dryRun", label: "Dry run flag", defaultValue: "--dry-run", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} drop-manifest`,
          `--manifest ${quote(v.manifest || DEFAULTS.manifest)}`,
          v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
      {
        id: "run-sql-file",
        label: "Run task SQL file",
        description: "Run task-local SQL such as anchor/distractor comment scripts.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "sqlFile", label: "SQL file", defaultValue: DEFAULTS.workspaceMetadataSql },
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
        id: "delete-workspace-path",
        label: "Delete workspace path",
        description: "Remove a Databricks Workspace notebook or folder, such as a utility notebook distractor.",
        fields: [
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile },
          { key: "workspacePath", label: "Workspace path", defaultValue: "/Workspace/Shared/utilities/fee_revenue_rank_direction_review.py" },
          {
            key: "recursive",
            label: "Recursive flag",
            defaultValue: "",
            options: [
              { value: "", label: "Off" },
              { value: "--recursive", label: "On (--recursive)" },
            ],
          },
          { key: "dryRun", label: "Dry run flag", defaultValue: "--dry-run", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/databricks_sdk_ops.py --profile ${v.profile || DEFAULTS.profile} delete-workspace-path`,
          `--workspace-path ${quote(v.workspacePath)}`,
          v.recursive ? "--recursive" : "",
          v.dryRun ? "--dry-run" : "",
        ]),
      },
    ],
  },
  {
    id: "notebooks",
    label: "Notebook Generation",
    description: "Generate task-local notebook assets from static specs, a JSON spec file, or the OpenAI API.",
    commands: [
      {
        id: "generate-task-notebooks",
        label: "Generate task notebooks",
        description: "Write notebook source files into a task's anchors/assets/notebooks or distractors/assets/notebooks folder and update manifests.",
        fields: [
          { key: "mode", label: "Mode", defaultValue: "distractors", options: OPTIONS.notebookMode, affectsVisibility: true },
          { key: "ids", label: "Notebook taxonomy IDs", defaultValue: "1.b.i,1.b.iii", taxonomyReference: true },
          { key: "specSource", label: "Spec source", defaultValue: "static", options: OPTIONS.specSource, affectsVisibility: true },
          { key: "specFile", label: "Spec JSON file", defaultValue: "", showWhen: (v) => v.specSource === "file" },
          { key: "specOut", label: "API-generated spec JSON", defaultValue: "tasks/meridian_mid_sized_bank/TASK-001-top-fee-revenue-branch/distractors/assets/notebooks/notebook_specs.json", showWhen: (v) => v.specSource === "api" },
          { key: "envFile", label: "Env file", defaultValue: DEFAULTS.envFile, showWhen: (v) => v.specSource === "api" },
          { key: "apiModel", label: "API model", defaultValue: "gpt-4.1-mini", showWhen: (v) => v.specSource === "api" },
          { key: "codeMode", label: "Code mode", defaultValue: "both", options: OPTIONS.codeMode },
          { key: "composition", label: "Composition", defaultValue: "separate", options: OPTIONS.composition },
          { key: "outDir", label: "Notebook output directory", defaultValue: DEFAULTS.notebooksOutDir },
          { key: "workspacePrefix", label: "Workspace prefix", defaultValue: DEFAULTS.workspacePrefix },
          { key: "anchorsManifest", label: "Anchor notebook manifest", defaultValue: DEFAULTS.anchorNotebookManifest },
          { key: "distractorsManifest", label: "Distractor notebook manifest", defaultValue: DEFAULTS.distractorNotebookManifest },
          { key: "dryRun", label: "Dry run flag", defaultValue: "", options: OPTIONS.dryRun },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m tools.generate_task_notebooks`,
          `--environment ${DEFAULTS.environment}`,
          `--mode ${v.mode || "distractors"}`,
          v.ids ? `--ids ${v.ids}` : "--all",
          `--spec-source ${v.specSource || "static"}`,
          v.specSource === "file" && v.specFile ? `--spec-file ${quote(v.specFile)}` : "",
          v.specSource === "api" ? `--spec-out ${quote(v.specOut)}` : "",
          v.specSource === "api" ? `--env-file ${quote(v.envFile || DEFAULTS.envFile)}` : "",
          v.specSource === "api" && v.apiModel ? `--api-model ${quote(v.apiModel)}` : "",
          `--code-mode ${v.codeMode || "both"}`,
          `--composition ${v.composition || "separate"}`,
          `--out-dir ${quote(v.outDir || DEFAULTS.notebooksOutDir)}`,
          `--workspace-prefix ${quote(v.workspacePrefix || DEFAULTS.workspacePrefix)}`,
          `--anchors-manifest ${quote(v.anchorsManifest || DEFAULTS.anchorNotebookManifest)}`,
          `--distractors-manifest ${quote(v.distractorsManifest || DEFAULTS.distractorNotebookManifest)}`,
          v.dryRun ? "--dry-run" : "",
        ]),
      },
    ],
  },
  {
    id: "genie",
    label: "Genie",
    description: "Build prompts/configs, create Genie spaces, ask Genie, and save the response under the task folder.",
    commands: [
      {
        id: "build-genie-prompt",
        label: "Build Genie prompt",
        description: "Build a task-local Genie prompt from task.yaml: question plus eval JSON contract only.",
        fields: [
          { key: "taskFile", label: "Task YAML", defaultValue: DEFAULTS.taskFile },
          { key: "minimalHint", label: "Minimal hint", defaultValue: "", options: OPTIONS.minimalHint },
          { key: "out", label: "Output prompt path", defaultValue: DEFAULTS.geniePromptOut },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/genie_prompt_builder.py ${quote(v.taskFile || DEFAULTS.taskFile)}`,
          v.minimalHint ? "--include-minimal-hint" : "",
          v.out ? `--out ${quote(v.out)}` : "",
        ]),
      },
      {
        id: "build-genie-space-config",
        label: "Build Genie Space config",
        description: "Create a Genie Space config using a task and generated schema JSON.",
        fields: [
          { key: "schemaDir", label: "JSON schema directory", defaultValue: DEFAULTS.schemaJsonDir },
          { key: "taskFile", label: "Task YAML", defaultValue: DEFAULTS.taskFile },
          { key: "out", label: "Output config JSON", defaultValue: DEFAULTS.genieSpaceConfig },
          { key: "title", label: "Space title", defaultValue: "Meridian Trust task space" },
          { key: "parentPath", label: "Parent workspace path", defaultValue: "/Workspace/Shared" },
          { key: "warehouseId", label: "SQL warehouse ID placeholder", defaultValue: DEFAULTS.warehouseId },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/build_genie_space_config.py`,
          `--environment ${DEFAULTS.environment}`,
          `--schema-dir ${quote(v.schemaDir || DEFAULTS.schemaJsonDir)}`,
          `--task ${quote(v.taskFile || DEFAULTS.taskFile)}`,
          `--out ${quote(v.out || DEFAULTS.genieSpaceConfig)}`,
          v.title ? `--title ${quote(v.title)}` : "",
          v.parentPath ? `--parent-path ${quote(v.parentPath)}` : "",
          v.warehouseId ? `--warehouse-id ${quote(v.warehouseId)}` : "",
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
      {
        id: "ask-genie",
        label: "Ask Genie with prompt",
        description: "Start a Genie conversation using a generated task prompt and save the JSON response.",
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
    id: "verify",
    label: "Task Verification",
    description: "Validate specs, build coverage, and run harness checks against saved Genie responses.",
    commands: [
      {
        id: "validate-tasks",
        label: "Validate task specs",
        description: "Run the task spec validator.",
        fields: [{ key: "tasksDir", label: "Tasks directory", defaultValue: "tasks" }],
        build: (v) => `${PYTHON} tools/validate_task_specs.py --tasks-dir ${quote(v.tasksDir || "tasks")}`,
      },
      {
        id: "coverage",
        label: "Build coverage matrix",
        description: "Create taxonomy coverage markdown from task declarations and harness reports.",
        fields: [
          { key: "tasksDir", label: "Tasks directory", defaultValue: "tasks/meridian_mid_sized_bank" },
          { key: "coverageOut", label: "Coverage output", defaultValue: "tasks/meridian_mid_sized_bank/coverage.md" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/coverage_matrix.py`,
          `--tasks-dir ${quote(v.tasksDir || "tasks/meridian_mid_sized_bank")}`,
          `--out ${quote(v.coverageOut || "tasks/meridian_mid_sized_bank/coverage.md")}`,
        ]),
      },
      {
        id: "verify-genie-response",
        label: "Verify Genie response",
        description: "Run the harness on a saved Genie response. Databricks executor uses the warehouse SQL dialect.",
        fields: [
          { key: "executor", label: "Executor", defaultValue: "databricks", options: OPTIONS.executor, affectsVisibility: true },
          { key: "taskFile", label: "Task YAML", defaultValue: DEFAULTS.taskFile },
          { key: "responseFile", label: "Saved Genie response", defaultValue: DEFAULTS.genieResponseOut },
          { key: "profile", label: "Databricks profile", defaultValue: DEFAULTS.profile, showWhen: (v) => v.executor === "databricks" },
          { key: "warehouseId", label: "SQL warehouse ID", defaultValue: DEFAULTS.warehouseId, showWhen: (v) => v.executor === "databricks" },
          { key: "dbPath", label: "SQLite DB path", defaultValue: DEFAULTS.sqliteOut, showWhen: (v) => v.executor === "sqlite" },
          { key: "out", label: "Harness report output", defaultValue: DEFAULTS.harnessOut },
          { key: "allowExtraTables", label: "Extra tables", defaultValue: "", options: OPTIONS.extraTables },
          { key: "llmSqlJudge", label: "LLM SQL judge", defaultValue: "", options: OPTIONS.llmJudge },
          { key: "llmModel", label: "LLM judge model", defaultValue: "gpt-4.1-mini", showWhen: (v) => Boolean(v.llmSqlJudge) },
          { key: "envFile", label: "Env file", defaultValue: DEFAULTS.envFile, showWhen: (v) => Boolean(v.llmSqlJudge) },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m harness.runner`,
          `--task ${quote(v.taskFile || DEFAULTS.taskFile)}`,
          `--response ${quote(v.responseFile || DEFAULTS.genieResponseOut)}`,
          `--executor ${v.executor || "databricks"}`,
          v.executor === "sqlite" ? `--db ${quote(v.dbPath || DEFAULTS.sqliteOut)}` : "",
          v.executor !== "sqlite" && v.profile ? `--profile ${v.profile}` : "",
          v.executor !== "sqlite" && v.warehouseId ? `--warehouse-id ${v.warehouseId}` : "",
          v.out ? `--out ${quote(v.out)}` : "",
          v.allowExtraTables ? "--allow-extra-tables" : "",
          v.llmSqlJudge ? "--llm-sql-judge" : "",
          v.llmSqlJudge && v.llmModel ? `--llm-model ${quote(v.llmModel)}` : "",
          v.llmSqlJudge && v.envFile ? `--env-file ${quote(v.envFile)}` : "",
        ]),
      },
    ],
  },
  {
    id: "utilities",
    label: "Utilities",
    description: "Small helper commands for local SQL inspection and task creation.",
    commands: [
      {
        id: "create-task",
        label: "Create task template",
        description: "Create a new task YAML from the shared task template.",
        fields: [
          { key: "taskId", label: "Task ID / filename stem", defaultValue: "TASK-011-new-task" },
          { key: "title", label: "Title", defaultValue: "Human-readable title" },
          { key: "question", label: "Question", defaultValue: "TBD - the natural-language question the agent receives.", multiline: true },
          { key: "tasksDir", label: "Tasks root directory", defaultValue: "tasks" },
          { key: "environment", label: "Environment", defaultValue: DEFAULTS.environment },
          { key: "overwrite", label: "Overwrite flag", defaultValue: "", options: OPTIONS.overwrite },
        ],
        build: (v) => joinCommand([
          `${PYTHON} tools/create_task.py`,
          `--task-id ${quote(v.taskId || "TASK-011-new-task")}`,
          v.title ? `--title ${quote(v.title)}` : "",
          v.question ? `--question ${quote(v.question)}` : "",
          `--tasks-dir ${quote(v.tasksDir || "tasks")}`,
          `--environment ${quote(v.environment || DEFAULTS.environment)}`,
          v.overwrite ? "--overwrite" : "",
        ]),
      },
      {
        id: "sqlite-query",
        label: "Run local SQL",
        description: "Run SQL against the local SQLite artifact while allowing canonical Databricks table names.",
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
          `--db ${quote(v.dbPath || DEFAULTS.sqliteOut)}`,
          `--sql ${quote(v.sql)}`,
          "--show-sql",
        ]),
      },
      {
        id: "sqlite-mapping",
        label: "List SQLite mapping",
        description: "Show how Databricks 3-part table names map to local SQLite table names.",
        fields: [{ key: "dbPath", label: "SQLite DB path", defaultValue: DEFAULTS.sqliteOut }],
        build: (v) => `${PYTHON} tools/sqlite_query.py --db ${quote(v.dbPath || DEFAULTS.sqliteOut)} --list-mapping`,
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
  document.getElementById("taxonomy-modal").addEventListener("click", (event) => {
    if (event.target.id === "taxonomy-modal") closeTaxonomyModal();
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
      if (field.affectsVisibility) renderFields();
      updateOutput();
    });
    input.addEventListener("change", (event) => {
      values[field.key] = event.target.value;
      if (field.affectsVisibility) renderFields();
      updateOutput();
    });
  });
}

function visibleFields(command, currentValues) {
  return command.fields.filter((field) => !field.showWhen || field.showWhen(currentValues));
}

function renderField(field) {
  const inputId = `field-${field.key}`;
  const currentValue = values[field.key] ?? field.defaultValue ?? "";
  const label = field.taxonomyReference
    ? `<div class="field-label-row"><label class="field-label" for="${inputId}">${escapeHtml(field.label)}</label><button type="button" class="taxonomy-button" data-taxonomy-open="true">View IDs</button></div>`
    : `<div class="field-label-row"><label class="field-label" for="${inputId}">${escapeHtml(field.label)}</label></div>`;
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

function pathJoin(base, child) {
  return `${String(base || "").replace(/\/+$/, "")}/${child.replace(/^\/+/, "")}`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
