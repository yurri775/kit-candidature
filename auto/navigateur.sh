#!/bin/sh
# Ouvre un navigateur pilotable (Chrome ou Brave) sur un profil SÉPARÉ, port CDP 9334.
# Connecte-toi une fois dedans (LinkedIn, Gmail…) : les scripts de auto/ s'y branchent ensuite.
PROFIL="$HOME/.kit_candidature_navigateur"
for APP in "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
           "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"; do
  if [ -x "$APP" ]; then
    exec "$APP" --remote-debugging-port="${CDP_PORT:-9334}" --user-data-dir="$PROFIL" --no-first-run "https://www.linkedin.com/login"
  fi
done
echo "Ni Brave ni Chrome trouvés dans /Applications" >&2; exit 1
