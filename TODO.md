# TODO

## Current status

- [x] Docker Compose architecture and private network defined.
- [x] MQTT broker, MongoDB, producer, analyzer, writer, and Node-RED are wired together.
- [x] Producer now uses NewsAPI ingestion plus synthetic mock mode.
- [x] Analyzer uses VADER sentiment scoring and ticker extraction.
- [x] MongoDB persists raw and analyzed events.
- [x] README is shortened and oriented to delivery.
- [x] Spanish memoria, notas, and presentación are aligned to the assignment.
- [x] Requirements audit file added for rubric mapping.
- [x] Dependencies stay isolated in containers and the local `.venv` workflow is documented.
- [x] `.gitignore` excludes virtualenv and cache artifacts.
- [x] `requirements-dev.txt` contains local tooling only.
- [x] `pyproject.toml` configures `pytest` and `ruff`.
- [x] CI workflow covers lint and tests.
- [x] Unit tests cover the pure logic of the three services.
- [x] Local `.venv` is created and selected in the project.
- [x] Development dependencies are installed in `.venv`.
- [x] `ruff check .` is green.
- [x] `pytest` is green.
- [x] Live NewsAPI article fetch validated with the configured API key.

## Remaining work for a polished delivery

### Priority 0: NewsAPI migration closure
- [ ] Export the Node-RED flow to PDF for the ZIP handoff.
- [ ] Capture a final screenshot of the dashboard for the presentation deck.
- [ ] If needed, run a live Docker round-trip with MongoDB populated from NewsAPI and then switch back to mock mode for a stable demo.

### Priority 1: broker and event design
- [x] Document the MQTT topic hierarchy, retained status message, and QoS choices in the final memory.
- [x] Make sure the dashboard subscribes to the analyzed and alert topics used by the updated producer and analyzer.

### Priority 2: demo and academic finish
- [x] Finalize the oral demo script and the last slide deck polish.
- [ ] Add integration tests for MQTT and Mongo if there is time left.

## Technical risks

- The live NewsAPI quota may require the mock mode for demos.
- The Node-RED dashboard must stay aligned with the new topics.
- The tests cover pure logic, but end-to-end validation still depends on Docker and MQTT runtime checks.

## Finish criteria

- The documentation should explain how to run the project without reading the code.
- The code should keep only useful comments, not noise.
- The local environment should live in `.venv`; nothing global beyond Docker and the base Python install.