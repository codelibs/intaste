# Assera UI

Assera UI is a Next.js 15 frontend application providing an intuitive interface for AI-assisted search powered by the Assera API.

## Features

- **Modern React with Next.js 15**: App Router, Server Components, and streaming
- **State Management**: Zustand for efficient client-side state
- **Type Safety**: Full TypeScript with strict mode
- **Styled Components**: Tailwind CSS with custom design system
- **Security**: XSS protection with DOMPurify, CSP headers
- **Responsive**: Mobile-first design with adaptive layouts
- **Accessible**: ARIA labels, keyboard navigation, screen reader support

## Quick Start

### Using Docker Compose (Recommended)

```bash
# From repository root
cd ..
make up
```

Access the UI at http://localhost:3000

### Local Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Project Structure

````
assera-ui/
├── app/                      # Next.js App Router
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Main search page
├── src/
│   ├── components/          # React components
│   │   ├── input/          # QueryInput
│   │   ├── answer/         # AnswerBubble
│   │   ├── sidebar/        # EvidencePanel, EvidenceItem
│   │   └── common/         # Shared components
│   ├── store/              # Zustand stores
│   │   ├── session.store.ts
│   │   ├── assist.store.ts
│   │   └── ui.store.ts
│   ├── libs/               # Utilities
│   │   ├── apiClient.ts    # API wrapper
│   │   ├── sanitizer.ts    # HTML sanitization
│   │   └── utils.ts        # Helpers
│   ├── types/              # TypeScript definitions
│   └── styles/             # Global styles
└── public/                 # Static assets

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_BASE` | `/api/v1` | API base path for client-side requests |
| `API_PROXY_URL` | - | Backend URL for server-side proxying (optional) |

## API Client

The UI communicates with Assera API using an authenticated fetch wrapper:

```typescript
import { queryAssist } from '@/libs/apiClient';

const response = await queryAssist({
  query: 'user question',
  session_id: 'optional-uuid',
  options: { max_results: 5 }
});
````

Authentication token is stored in localStorage and sent via `X-Assera-Token` header.

## Components

### QueryInput

Multi-line text input with keyboard shortcuts:

- `Enter`: Submit query
- `Shift+Enter`: New line
- Max 4096 characters

### AnswerBubble

Displays LLM-generated answer with:

- Citation references `[1]`, `[2]`, etc. (clickable)
- Suggested follow-up questions
- Fallback notices

### EvidencePanel

Sidebar with two tabs:

- **Selected**: Detailed view of one citation
- **All**: List of all citations

### EvidenceItem

Citation card showing:

- Title and snippet (sanitized HTML)
- Metadata (site, type, score)
- "Open in Fess" link

## State Management

Three Zustand stores:

1. **Session Store** (`useSessionStore`)
   - Conversation session ID and turn tracking

2. **Assist Store** (`useAssistStore`)
   - Search state, results, citations
   - Loading and error states
   - `send()` method for queries

3. **UI Store** (`useUIStore`)
   - Theme, language, preferences
   - API token management
   - Persisted to localStorage

## Security

- **XSS Protection**: DOMPurify sanitizes HTML snippets
- **CSP Headers**: Restrictive content security policy
- **Token Storage**: API token in localStorage (user-provided)
- **URL Validation**: External links checked against whitelist

## Development

### Scripts

```bash
npm run dev          # Development server (hot reload)
npm run build        # Production build
npm start            # Start production server
npm run lint         # ESLint check
npm run type-check   # TypeScript check
npm run format       # Prettier format
```

### Adding Components

Follow the established patterns:

1. Create component in appropriate directory
2. Add Apache License header
3. Use TypeScript with proper types
4. Include accessibility attributes
5. Use Tailwind CSS for styling

## Deployment

### Docker

```bash
# Build image
docker build -t assera-ui:latest .

# Run container
docker run -d \
  --name assera-ui \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_BASE=/api/v1 \
  assera-ui:latest
```

### Production Considerations

- Use environment-specific API endpoints
- Enable Next.js telemetry monitoring
- Configure CDN for static assets
- Set up proper CSP policies
- Use HTTPS with proper certificates

## Testing

### Quick Start

```bash
# Run unit tests
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e

# Run E2E with UI
npm run test:e2e:ui
```

### Test Structure

- `tests/` - Unit tests
  - `components/` - Component tests (QueryInput, AnswerBubble, EvidenceItem)
  - `stores/` - State management tests (assist, ui, session stores)
  - `utils/` - Test utilities and helpers
- `e2e/` - End-to-end tests
  - `search-flow.spec.ts` - Main search functionality
  - `citation-interaction.spec.ts` - Citation clicking and navigation
  - `accessibility.spec.ts` - Accessibility compliance

### Technologies

- **vitest** - Fast unit test framework
- **@testing-library/react** - Component testing utilities
- **@playwright/test** - E2E testing across browsers
- **jsdom** - DOM simulation for unit tests

### Coverage

View coverage report:

```bash
npm run test:coverage
open coverage/index.html
```

For more details, see [../TESTING.md](../TESTING.md)

## Browser Support

- Chrome/Edge: Latest + 1
- Firefox: Latest + 1
- Safari: Latest + 1
- Mobile: iOS Safari, Chrome Android

## License

Copyright (c) 2025 CodeLibs

Licensed under the Apache License, Version 2.0. See [LICENSE](../LICENSE) file for details.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Discussions**: Ask questions and share ideas via GitHub Discussions
