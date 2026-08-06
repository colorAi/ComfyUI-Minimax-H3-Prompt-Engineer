# ComfyUI Registry publishing

The ComfyUI Registry is the package source used by ComfyUI-Manager. This repository is configured for manual, reviewed releases.

## Registry identity

- Node ID: `minimax-h3-prompt-engineer`
- Display name: `MiniMax H3 Prompt Engineer`
- Publisher ID: `hootoo`
- Repository: `https://github.com/colorAi/ComfyUI-Minimax-H3-Prompt-Engineer`

The node ID and Publisher ID are permanent Registry identifiers. Confirm that the `hootoo` Publisher exists in the ComfyUI Registry before the first release.

## One-time setup

1. Sign in at `https://registry.comfy.org`.
2. Create or select the `hootoo` Publisher.
3. Create a Registry publishing API key for that Publisher.
4. Install `comfy-cli` and authenticate it with the Registry key.

## Release checklist

1. Update the semantic version in `pyproject.toml`, `__init__.py`, both client User-Agent strings, and both README version badges.
2. Add the release notes to `CHANGELOG.md`.
3. Run:

   ```bash
   python -m unittest discover -s tests -v
   python -m compileall -q .
   node --check web/h3_asset_autocomplete.js
   git diff --check
   ```

4. Confirm that `pyproject.toml`, `requirements.txt`, `LICENSE`, `README.md`, `node_list.json`, both H3 writing guides, Python modules, examples, and `web/` are present in the publish archive.
5. Push the reviewed release commit and tag to GitHub.
6. From the repository root, publish the package:

   ```bash
   comfy node publish
   ```

7. Verify the Registry listing, extracted node list, installation through ComfyUI-Manager, and a clean ComfyUI restart.
