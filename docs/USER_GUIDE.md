# FORGE Desktop User Guide

A step-by-step walkthrough for building an integration with FORGE.

## 1. Opening or Creating a Project
1. Launch FORGE: `forge gui`.
2. Navigate to **Projects** from the sidebar.
3. Enter a project name and directory path, then click **Create / Open**.

## 2. Editing the Integration Manifest
1. Navigate to **Manifest Studio**.
2. Click **Load FixtureLab Template** or **Load Blender Template**.
3. Review capabilities and click **Validate Manifest**.
4. Click **Save to Workspace**.

## 3. Generating the Connector
1. Navigate to **Builds & Generator**.
2. Click **Generate Connector from Manifest**.
3. Inspect generated files in the right panel.

## 4. Running Tests in the Test Lab
1. Navigate to **Test Lab**.
2. Click **Run Verification Suites**.
3. View real-time results and logs.

## 5. Reviewing Approvals
1. In **Tool Explorer**, invoke a mutating tool.
2. The gateway registers a pending approval.
3. Open **Approvals**, review the arguments, and click **Approve Once**.

## 6. Exporting Packages
1. Open **Packages**.
2. Click **Package Latest Build (ZIP)**.
3. Click **Copy Config JSON** to configure your MCP client.
