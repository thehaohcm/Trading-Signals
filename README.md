# trading-vue

## Project setup
```
yarn install
```

### Compiles and hot-reloads for development
```
yarn serve
```

### Compiles and minifies for production
```
yarn build
```

### Lints and fixes files
```
yarn lint
```

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).
# Trading-Signals

## NotebookLM authentication

Run these commands from the project root in PowerShell. The script reads server
settings from `osint_ai_worker/.env` and uploads the authenticated
`storage_state.json` to the configured server.

Install the required NotebookLM dependencies in the project virtual environment:

```powershell
& .\.venv\Scripts\python.exe -m pip install "notebooklm-py[headless,browser,cookies]>=0.8.2"
```

Log in using the cookies from the currently signed-in Chrome profile and upload
the authentication file:

```powershell
& .\.venv\Scripts\python.exe .\scripts\login_upload_notebooklm.py --browser-cookies chrome
```

For another Chrome profile, use its profile name:

```powershell
& .\.venv\Scripts\python.exe .\scripts\login_upload_notebooklm.py --browser-cookies "chrome::Profile 1"
```

To upload the existing local authentication file without logging in again:

```powershell
& .\.venv\Scripts\python.exe .\scripts\login_upload_notebooklm.py --skip-login
```
