This folder contains lightweight React Three Fiber components used by the Home dashboard.

Files
- FarmScene.tsx: A minimal farm scene (ground + simple barn) that accepts a `devices` prop and `onToggleDevice` callback.
- DeviceMarker.tsx: Small interactive device marker with a label and hover/click behavior.
- FarmHUD.tsx: Simple HUD with buttons to simulate irrigation and toggle devices.
- Farm3DContainer.tsx: Container that manages device state and wires HUD actions to the scene.

Extending with real 3D models
- Place GLTF/GLB files under `public/models/` and load them with `useGLTF('/models/your-model.glb')` inside `FarmScene`.
- Consider using `GLTFLoader` with DRACO compression for smaller downloads.

Performance tips
- Lazy-load the 3D scene with Suspense and code-splitting (dynamic import) so initial page render is fast.
- Use low-poly models, texture atlases, and instancing for repeated objects (trees, plants).
- Limit shadow casting and prefer baked lighting for static elements.

Integrating AI/ML
- For heavy ML tasks, call backend endpoints (FastAPI) and stream results via WebSockets or Server-Sent Events.
- For lightweight on-device inference, consider `@tensorflow/tfjs` and load a small model in a Web Worker.

This README is a short guide — see project-level docs for deployment and model-serving patterns.
