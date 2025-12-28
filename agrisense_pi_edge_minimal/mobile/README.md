# AgriSense Mobile (Expo)

A minimal React Native (Expo) companion app to monitor tank status, see last recommendation, and start/stop irrigation.

## Features (MVP)
- Show tank status (level %, volume, last update)
- Show last recommendation summary including water_source
- Quick actions: Start (10 min), Stop irrigation for zone Z1

## Project setup
This is a lightweight template using Expo Router and TypeScript.

Prerequisites:
- Node.js 18+
- Expo CLI (npx is fine)

## How to run
1. Install deps
   - Windows PowerShell:
     npx --yes expo@latest install
     npm install
2. Start the app
   - Windows PowerShell:
     npx expo start --tunnel
3. Open on device with Expo Go (Android/iOS) or run an emulator/simulator.

## Configuration
- API base URL is read from environment `EXPO_PUBLIC_API_URL`.
  - During local dev with the web frontend using Vite proxy, set it to `http://localhost:8004` (your FastAPI backend port).
  - Example (PowerShell):
    $env:EXPO_PUBLIC_API_URL = "http://localhost:8004"; npx expo start --tunnel

## Folder layout
- app/            Expo Router screens
- app/_layout.tsx Shell + theme provider
- app/index.tsx   Dashboard screen
- lib/api.ts      Minimal API client (shared shapes with web)
- components/     Small UI bits

## Next steps
- Add login or simple PIN if needed
- Multi-zone support and dynamic zone/tank IDs
- Push notifications (Expo Notifications)
- Offline cache (React Query + MMKV)
