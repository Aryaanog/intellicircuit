# IntelliCircuit 🤖⚡
> **An AI-Powered Hardware Design & EDA Compiler**

IntelliCircuit is an advanced, electronic design automation (EDA) software suite that translates abstract, natural-language hardware requirements into fully validated schematic graph topologies and production-ready PCB netlists. By bypassing manual schematic data entry, the system serves as an intelligent hardware compiler that maps physical peripheral networks deterministically.

---

## 🏗️ Architecture Overview

The repository is organized into a completely decoupled full-stack architecture:

```text
intellicircuit/
├── backend/          # Asynchronous FastAPI web server & AI synthesis pipelines
└── frontend/         # React SPA dashboard with live visual graph workspaces