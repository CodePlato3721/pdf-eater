## Coding Standards

- **Keep frontend TSX lightweight**: Components are responsible only for rendering; state, side effects, and event handlers must be extracted into custom hooks (`use*`). Hooks go in the same directory as the component or under a `hooks/` directory; test files go alongside the hook (`useXxx.test.ts`).
- **Frontend unit tests follow the Chicago style**: Mocks are used only to make the code under test runnable (isolating external dependencies, controlling return values). Do not assert how many times a mock was called or with what arguments. Assert only observable state results.
- **The backend root directory contains only entry-point files** (main.py and FastAPI endpoint registrations); session state, business orchestration, and other service-layer code go in `backend/services/`; domain capabilities go in `backend/core/`.
- **The backend `AppState` (`services/state.py`) is a pure state container and self-persistence handler**; business orchestration (upload pipeline, Q&A, etc.) goes in independent service modules under `services/`; endpoints handle only HTTP mapping and exception translation.
- **Do not write unit tests for backend main.py endpoints (pure HTTP mapping and exception translation)**; verify behavior through unit tests on the services/core/state layer by calling functions directly, not through HTTP.

## NEVER

- **No magic numbers or magic strings**: When a numeric or string literal carries semantic meaning, it must be extracted into a named constant (`const` object with `as const`, or a plain `const`). Literals may be used inline only when: the value is a discriminant of a discriminated union (e.g. `event.type === 'token'`), appears in exactly one place, and its meaning is completely self-evident.
