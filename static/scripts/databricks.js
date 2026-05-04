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
  workspaceMetadataSql: "eval/workspace_metadata/TASK-001-short-slug_metadata.sql",
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
  extraTables: [
    { value: "", label: "Fail extra tables" },
    { value: "--allow-extra-tables", label: "Allow extra tables" },
  ],
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
    ],
  },
  {
    id: "generate",
    label: "Generate",
    commands: [
      {
        id: "generate-data",
        label: "Generate gold + asset data",
        description: "Build gold tables plus generated table anchors and table distractors.",
        fields: [
          { key: "sqliteOut", label: "SQLite output", defaultValue: DEFAULTS.sqliteOut },
          { key: "csvDir", label: "CSV output directory", defaultValue: DEFAULTS.csvDir },
          { key: "schemaJsonDir", label: "JSON schema directory", defaultValue: DEFAULTS.schemaJsonDir },
          { key: "seed", label: "Seed", defaultValue: "42" },
          { key: "scale", label: "Scale", defaultValue: "1.0" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.generators.run`,
          "--target sqlite",
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
        id: "generate-selected-assets",
        label: "Generate selected asset data",
        description: "Build gold tables plus selected anchor/distractor asset tables by taxonomy ID.",
        fields: [
          { key: "anchorTypes", label: "Anchor taxonomy IDs", defaultValue: "1.a.i,2.a.ii", taxonomyReference: true },
          {
            key: "distractorTypes",
            label: "Distractor taxonomy IDs",
            defaultValue: "1.a.i,1.a.viii",
            taxonomyReference: true,
          },
          { key: "sqliteOut", label: "SQLite output", defaultValue: "verification/runs/selected_assets_seed.sqlite" },
          { key: "csvDir", label: "CSV output directory", defaultValue: "verification/exports/selected_assets_csv" },
          { key: "schemaJsonDir", label: "JSON schema directory", defaultValue: "verification/schema/selected_assets_json" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.generators.run`,
          "--target sqlite",
          `--anchor-types ${v.anchorTypes || "1.a.i,2.a.ii"}`,
          `--distractor-types ${v.distractorTypes || "1.a.i,1.a.viii"}`,
          `--out ${quote(v.sqliteOut)}`,
          `--csv-dir ${quote(v.csvDir)}`,
          `--schema-json-dir ${quote(v.schemaJsonDir)}`,
        ]),
      },
      {
        id: "generate-random-assets",
        label: "Generate random asset data",
        description: "Build gold tables plus randomly sampled anchor/distractor asset tables.",
        fields: [
          { key: "randomAnchors", label: "Random anchor count", defaultValue: "2" },
          { key: "randomDistractors", label: "Random distractor count", defaultValue: "3" },
          { key: "seed", label: "Seed", defaultValue: "17" },
          { key: "sqliteOut", label: "SQLite output", defaultValue: "verification/runs/random_assets_seed.sqlite" },
          { key: "csvDir", label: "CSV output directory", defaultValue: "verification/exports/random_assets_csv" },
          { key: "schemaJsonDir", label: "JSON schema directory", defaultValue: "verification/schema/random_assets_json" },
        ],
        build: (v) => joinCommand([
          `${PYTHON} -m workspace.generators.run`,
          "--target sqlite",
          `--random-anchors ${v.randomAnchors || "2"}`,
          `--random-distractors ${v.randomDistractors || "3"}`,
          `--seed ${v.seed || "17"}`,
          `--out ${quote(v.sqliteOut)}`,
          `--csv-dir ${quote(v.csvDir)}`,
          `--schema-json-dir ${quote(v.schemaJsonDir)}`,
        ]),
      },
      {
        id: "generate-notebooks",
        label: "Generate notebooks",
        description: "Create notebook assets and update notebook manifests.",
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
        label: "Generate LLM notebook specs",
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
    label: "Genie",
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
    ],
  },
  {
    id: "tasks",
    label: "Tasks",
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
          { key: "responseFile", label: "Saved Genie response", defaultValue: "verification/responses/TASK-001-genie.txt" },
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
        id: "sqlite-query",
        label: "Run local SQL",
        description: "Run SQL against SQLite while allowing canonical table names.",
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
    ],
  },
  {
    id: "prompts",
    label: "Prompts",
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
  container.innerHTML = activeCommand.fields.map((field) => renderField(field)).join("");
  activeCommand.fields.forEach((field) => {
    const input = document.getElementById(`field-${field.key}`);
    input.addEventListener("input", (event) => {
      values[field.key] = event.target.value;
      updateOutput();
    });
    input.addEventListener("change", (event) => {
      values[field.key] = event.target.value;
      updateOutput();
    });
  });
}

function renderField(field) {
  const inputId = `field-${field.key}`;
  const label = field.taxonomyReference
    ? `<div class="field-label-row"><label class="field-label" for="${inputId}">${escapeHtml(field.label)}</label><button type="button" class="taxonomy-button" data-taxonomy-open="true">View IDs</button></div>`
    : `<label class="field-label" for="${inputId}">${escapeHtml(field.label)}</label>`;
  if (field.options) {
    const options = field.options.map((option) => {
      const value = typeof option === "string" ? option : option.value;
      const text = typeof option === "string" ? option : option.label;
      const selected = value === (field.defaultValue || "") ? "selected" : "";
      return `<option value="${escapeHtml(value)}" ${selected}>${escapeHtml(text)}</option>`;
    }).join("");
    return `<div>${label}<select id="${inputId}" class="command-control">${options}</select></div>`;
  }
  if (field.multiline) {
    return `<div>${label}<textarea id="${inputId}" class="command-textarea">${escapeHtml(field.defaultValue || "")}</textarea></div>`;
  }
  return `<div>${label}<input id="${inputId}" class="command-control" value="${escapeHtml(field.defaultValue || "")}"></div>`;
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
