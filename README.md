# dev-workplace (plantilla)

Plantilla reutilizable del flujo de trabajo Solopreneur. Ver `CLAUDE.md` para las reglas
del proyecto (arquitectura la decide el CEO, estándar de código Clean Code, etc.).

## CI/CD

El pipeline vive en `.github/workflows/ci.yml` y corre en cada PR hacia `dev` o `main`.
No usa ninguna API de pago: el review con IA corre en un modelo local vía Ollama.

### 1. Job `checks` (siempre corre)

- **Lint** y **tests unitarios**: hoy son placeholders (`echo "TODO..."`) porque este
  repo es una plantilla y el stack real todavía no está decidido. Cuando se decida,
  reemplazar esos dos steps en `ci.yml` — ahí mismo hay comentarios con ejemplos para
  Python, Node/TS, Go y Rust.
- **Análisis del diff**: cuenta las líneas cambiadas (insertions + deletions) contra el
  base del PR y chequea si algún archivo modificado empieza con alguna de las rutas
  listadas en `.github/sensitive-paths.txt`.

### 2. Job `local-review` (condicional)

Se dispara solo si:

- el diff cambia más de **80 líneas** (ajustable en `env.DIFF_LINE_THRESHOLD` dentro de
  `.github/workflows/ci.yml`), **o**
- toca alguna carpeta listada en `.github/sensitive-paths.txt` (por defecto: `auth/`,
  `payments/`, `security/`, `migrations/` — ajustable editando ese archivo, una ruta por
  línea).

Corre en un **runner self-hosted** (label `self-hosted`) y hace lo siguiente:

1. Obtiene el diff del PR.
2. Chequea que Ollama esté disponible en `http://localhost:11434`.
3. Le manda el diff al modelo local (`qwen2.5:7b` por defecto) vía la API de Ollama
   (`POST /api/generate`).
4. Postea la respuesta como comentario en el PR usando la GitHub API (`gh pr comment`,
   con el `GITHUB_TOKEN` que Actions provee automáticamente — no hace falta un token
   propio).

**Si Ollama no está disponible** (timeout o conexión rechazada), el job **falla
explícitamente** con un mensaje `"review local no disponible, revisar manualmente"` —
nunca da un OK falso ni bloquea el merge en silencio. Si el check está marcado como
requerido en la protección de rama, el PR queda bloqueado hasta que alguien revise a
mano o el runner/Ollama vuelvan a estar disponibles.

#### Cambiar el modelo de Ollama

Bajar el modelo en la máquina del runner y actualizar `env.OLLAMA_MODEL` en
`.github/workflows/ci.yml`:

```bash
ollama pull llama3.1:8b   # o el modelo que se quiera usar
```

```yaml
# .github/workflows/ci.yml, job local-review
env:
  OLLAMA_MODEL: llama3.1:8b
```

### 3. `/solopreneur:review` — revisión manual, no automática

`/solopreneur:review` (del plugin Solopreneur) **no** corre en el pipeline. Queda
disponible para que el CEO lo invoque a mano cuando el reviewer local (un modelo de ~7B
corriendo en localhost) no cubre bien un caso — típicamente lógica de negocio compleja
que necesita más razonamiento que el que puede dar un modelo chico local.

## Runner self-hosted en la máquina Arch/CachyOS

El job `local-review` necesita un runner registrado con la label `self-hosted` en esta
máquina (donde corre Ollama). Pasos reales para registrarlo (reemplazar `<TOKEN>` con el
valor que te da el comando de `gh api`):

```bash
# 1. Crear una carpeta para el runner y entrar
mkdir -p ~/actions-runner && cd ~/actions-runner

# 2. Descargar el paquete del runner (chequear la última versión en
#    https://github.com/actions/runner/releases y ajustar la URL/versión)
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/latest/download/actions-runner-linux-x64-<VERSION>.tar.gz
tar xzf actions-runner-linux-x64.tar.gz

# 3. Pedir un token de registro para este repo con gh (ya autenticado con `gh auth login`)
TOKEN=$(gh api -X POST repos/yeahtosty/dev-workplace/actions/runners/registration-token --jq .token)

# 4. Configurar el runner con ese token y la label "self-hosted"
./config.sh --url https://github.com/yeahtosty/dev-workplace --token "$TOKEN" --labels self-hosted

# 5a. Correrlo en foreground (para probar)
./run.sh

# 5b. O instalarlo como servicio systemd para que quede corriendo siempre
sudo ./svc.sh install
sudo ./svc.sh start
```

Alternativa sin `gh api`: ir a **Settings → Actions → Runners → New self-hosted runner**
en `https://github.com/yeahtosty/dev-workplace`, que muestra los mismos comandos con el
token ya generado.

Requisito previo en esta máquina: Ollama corriendo y accesible en `localhost:11434`, con
el modelo default ya bajado:

```bash
ollama pull qwen2.5:7b
```

## Ajustar los umbrales del review condicional

| Qué ajustar | Dónde |
|---|---|
| Umbral de líneas cambiadas (default: 80) | `env.DIFF_LINE_THRESHOLD` en `.github/workflows/ci.yml` |
| Carpetas/rutas sensibles | `.github/sensitive-paths.txt` (una ruta por línea, funciona como prefijo) |
| Modelo de Ollama (default: `qwen2.5:7b`) | `env.OLLAMA_MODEL` en el job `local-review` de `.github/workflows/ci.yml` |
