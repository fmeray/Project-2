# Coding-agent rules

- Keep primary and secondary knowledge-base sources separate.
- Treat primary FREITAG documents as authoritative over secondary research.
- Do not invent product, brand, price, availability, or impact claims.
- Keep API keys in `.env`; never commit real credentials.
- Preserve source paths in retrieved context so outputs can be reviewed.
- Keep prompt templates reusable and stored in `templates/`.
- Use mocked LLM calls when testing pipeline logic.
- Require human review before generated content is published.
