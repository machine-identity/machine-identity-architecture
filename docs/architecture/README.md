# Architecture Diagrams

Mermaid diagrams for the Machine Identity Architecture paper.

## Diagrams

| File | Description |
|------|-------------|
| `identity-spectrum.mmd` | Sovereign vs Accountable models + Convergence architecture |
| `sovereign-bootstrap.mmd` | 6-Phase Autonomous Identity Bootstrapping Pipeline |
| `control-layers.mmd` | Three enforcement layers preventing rogue agents |
| `economic-model.mmd` | Laffer Curve of Machine Taxation & Survival Math |

## Viewing

### Online
- Paste `.mmd` content into [Mermaid Live Editor](https://mermaid.live/)
- GitHub renders Mermaid natively in markdown files

### Local (VS Code)
```bash
# Install Mermaid preview extension
code --install-extension bierner.markdown-mermaid
```

### CLI
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Render to SVG
mmdc -i identity-spectrum.mmd -o identity-spectrum.svg
```

## Embedding in Markdown
```markdown
```mermaid
[diagram content here]
```
```

## License

Diagrams are part of the research paper and are licensed under [CC-BY-4.0](../../LICENSE-CC-BY-4.0.txt).