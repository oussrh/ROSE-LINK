# ROSE Link Website

The official landing page for ROSE Link - Home VPN Router + Ad Blocking on Raspberry Pi.

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Deployment**: Vercel (Static Export)

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint
```

## Deployment

This site is configured for static export and can be deployed to Vercel with zero configuration:

1. Push to GitHub
2. Import the `website` folder in Vercel
3. Deploy automatically

Or deploy manually:

```bash
npm run build
# Upload the 'out' folder to any static hosting
```

## Structure

```
website/
├── src/
│   ├── app/
│   │   ├── layout.tsx      # Root layout with metadata
│   │   ├── page.tsx        # Home page
│   │   └── globals.css     # Global styles
│   └── components/
│       ├── Navbar.tsx      # Navigation bar
│       ├── Hero.tsx        # Hero section
│       ├── Features.tsx    # Features grid
│       ├── Roadmap.tsx     # Roadmap/improvements
│       ├── Installation.tsx # Installation guide
│       ├── OpenSource.tsx  # Open source benefits
│       ├── Documentation.tsx # Docs links
│       └── Footer.tsx      # Footer
├── public/                 # Static assets
├── tailwind.config.ts     # Tailwind configuration
├── next.config.ts         # Next.js configuration
└── vercel.json            # Vercel configuration
```

## License

MIT - Same as the main ROSE Link project.
