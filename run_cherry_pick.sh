#!/bin/bash
set -e

FILES=(
"backend/app/routes/round1.py"
"backend/app/services/auth_service.py"
"backend/app/services/round1_service.py"
"frontend/src/main.jsx"
"frontend/src/index.css"
"frontend/src/pages/LandingGlitch.jsx"
"frontend/src/pages/Round1.jsx"
"frontend/src/pages/Round1PreLobby.jsx"
"frontend/src/pages/Round2Lobby.jsx"
"frontend/src/components/ChronosIntro.jsx"
"frontend/src/components/ChronosTitle.jsx"
"frontend/src/components/CrtShutdown.jsx"
"frontend/src/utils/audio.js"
"frontend/package.json"
"frontend/vite.config.js"
"frontend/index.html"
"frontend/.gitignore"
"start.sh"
"PROJECT_REFERENCE.md"
)

for f in "${FILES[@]}"; do
    git show "upstream/main:$f" > "$f"
done

NEW_FILES=(
"backend/seed_round1.py"
"backend/seed_round2.py"
"backend/optimize_round1_images.py"
"frontend/src/styles/round1.css"
"start.bat"
)
for f in "${NEW_FILES[@]}"; do
    mkdir -p "$(dirname "$f")"
    git show "upstream/main:$f" > "$f" || true
done

