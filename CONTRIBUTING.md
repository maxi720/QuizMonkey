## Contributing

Thanks for your interest in contributing to QuizApp.

### Project scope

- QuizApp is a Flet app with a single main code file: `src/main.py`.
- Quiz data is CSV-based and follows the format documented in `README.md`.

### Getting started

1. Fork the repository.
2. Create a feature branch from `main`.
3. Run the app locally:

```bash
uv run flet run
```

For web mode:

```bash
uv run flet run --web
```

### Development guidelines

- Keep changes focused and small.
- Preserve compatibility with `flet==0.82.0`.
- Use uppercase Flet enums/namespaces (for example `ft.Colors.BLUE`).
- Do not add unrelated refactors in feature fixes.
- Keep UI responsive for phone, tablet, and desktop widths.

### CSV-related changes

If you touch quiz loading or validation, ensure:

- Delimiter is `;`.
- Exactly 6 fields per row.
- No header row.
- `correctAnswer` exactly matches one answer option.

### Pull request checklist

- [ ] Change is scoped and explained clearly.
- [ ] App starts and runs in desktop mode.
- [ ] If UI changed, basic responsive behavior was checked.
- [ ] If CSV logic changed, valid and invalid CSV cases were tested.
- [ ] Documentation updated (`README.md`) when needed.

### Commit messages

Use short, clear messages in imperative style, for example:

- `fix csv validation edge case`
- `improve result view spacing on mobile`

### Code of conduct

Please be respectful and constructive in all discussions.
