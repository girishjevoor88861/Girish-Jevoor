# CivicAI - Operational Limitations & Engineering Boundaries

This document transparently outlines the boundaries of the current CivicAI platform implementation, distinguishing actual AI capabilities, algorithmic routines, and future enterprise expansion targets.

---

## 1. Actual vs. Algorithmic Features

| Module | Implemented Architecture | External Dependencies | Operational Boundaries |
| :--- | :--- | :--- | :--- |
| **NLP Classification** | Local tokenization, N-gram extraction, and municipal taxonomy scoring (35 subcategories across 7 departments). | None (zero cloud latency). | Highly accurate on municipal domain terminology; handles slang via keyword mapping, but does not parse unstructured foreign language idioms. |
| **Duplicate Detection** | Multi-modal formula combining Jaccard word token overlap, character 3-gram similarity, and Haversine geographic distance (< 350m). | None. | Optimized for geographic proximity and text overlap. Extreme misspellings or non-English text may reduce similarity percentage. |
| **Priority Engine** | 5-factor weighted formula (Safety 30%, Impact 25%, Urgency 20%, Concentration 15%, Frequency 10%) with regex life-hazard overrides. | None. | Fully deterministic and explainable; avoids neural halluncination. Weights are configurable via `backend/config.py`. |
| **Hotspot Intelligence** | Pure Python DBSCAN implementation with great-circle Haversine distance metric ($\epsilon = 0.65\text{ km}$, $\text{MinPts} = 3$). | None. | Computes density clusters across hundreds of active complaints instantaneously. For cities with >100,000 active complaints, a spatial index (e.g. PostGIS R-Tree) is recommended. |

---

## 2. Infrastructure & Persistence

- **Database**: The current release uses SQLite 3 with Write-Ahead Logging (`WAL` mode). This allows concurrent reads and high transaction throughput. In multi-million record distributed setups, migration to PostgreSQL with Supabase or PostGIS can be achieved using identical relational table schemas.
- **File Storage**: Uploaded photographic evidence is stored in the local `uploads/` directory with sanitized filenames. Production enterprise deployments should map this to AWS S3, Google Cloud Storage, or Azure Blob Storage.
- **SMS / Email Alerts**: The platform includes a full in-app notification center with read/unread tracking. External transactional SMS (Twilio) or SMTP email services require adding credentials to `.env`.

---

## 3. Recommended Future Roadmap

1. **Multilingual NLP**: Support for regional vernacular languages via multilingual transformer embeddings (e.g. mBERT).
2. **Computer Vision Verification**: Automatic validation of before/after photos using object detection (e.g. pothole segmentation model) to automatically verify whether asphalt patching is complete.
3. **IoT Sensor Ingestion**: Direct integration with municipal SCADA drainage level sensors and smart streetlight telemetry.
