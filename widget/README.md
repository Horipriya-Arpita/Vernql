# Vernql Embeddable Widget

A beautiful, drop-in chat widget that brings natural language to SQL conversion to any website.

## Features

- ✅ **Universal Compatibility** - Works with any tech stack (React, Vue, WordPress, PHP, etc.)
- ✅ **Zero Build Process** - Just add 2 script tags
- ✅ **Beautiful UI** - Modern chat interface with dark mode support
- ✅ **Mobile Responsive** - Optimized for all screen sizes
- ✅ **Customizable** - Theme, position, colors, and text
- ✅ **Secure** - iframe-based sandboxing
- ✅ **Lightweight** - Fast loading with minimal overhead

## Quick Start

### 1. Add the Widget to Your Website

Add this code to your HTML, just before the closing `</body>` tag:

```html
<!-- Vernql Widget -->
<script src="https://cdn.vernql.com/widget.js"></script>
<script>
  Vernql.init({
    apiKey: 'YOUR_API_KEY',
    schemaId: 'YOUR_SCHEMA_ID'
  })
</script>
```

### 2. Get Your API Key

1. Visit your Vernql dashboard at `/dashboard/api-keys`
2. Generate a new API key
3. Copy and replace `YOUR_API_KEY` in the code above

### 3. Get Your Schema ID

1. Visit your Vernql dashboard at `/dashboard/schemas`
2. Upload your database schema
3. Copy the schema ID
4. Replace `YOUR_SCHEMA_ID` in the code above

That's it! The widget will appear in the bottom-right corner of your website.

## Configuration Options

```javascript
Vernql.init({
  // Required
  apiKey: 'your-api-key',        // Your Vernql API key
  schemaId: 'your-schema-id',    // The schema ID to query

  // Optional
  apiUrl: 'http://localhost:8000',  // Your Vernql API endpoint (default: http://localhost:8000)
  theme: 'auto',                    // 'light' | 'dark' | 'auto' (default: 'auto')
  position: 'bottom-right',         // 'bottom-right' | 'bottom-left' (default: 'bottom-right')
  title: 'SQL Assistant',           // Custom widget title
  placeholder: 'Ask a question...'  // Custom input placeholder
})
```

## Framework-Specific Integration

### React / Next.js

```jsx
import { useEffect } from 'react'

export default function MyPage() {
  useEffect(() => {
    const script = document.createElement('script')
    script.src = 'https://cdn.vernql.com/widget.js'
    script.onload = () => {
      window.Vernql.init({
        apiKey: process.env.NEXT_PUBLIC_VERNQL_API_KEY,
        schemaId: process.env.NEXT_PUBLIC_VERNQL_SCHEMA_ID,
        theme: 'auto',
        position: 'bottom-right'
      })
    }
    document.body.appendChild(script)

    return () => {
      window.Vernql?.destroy()
      document.body.removeChild(script)
    }
  }, [])

  return <div>My App</div>
}
```

### Vue.js

```vue
<template>
  <div>My App</div>
</template>

<script>
export default {
  mounted() {
    const script = document.createElement('script')
    script.src = 'https://cdn.vernql.com/widget.js'
    script.onload = () => {
      window.Vernql.init({
        apiKey: process.env.VUE_APP_VERNQL_API_KEY,
        schemaId: process.env.VUE_APP_VERNQL_SCHEMA_ID,
        theme: 'auto',
        position: 'bottom-right'
      })
    }
    document.body.appendChild(script)
  },
  beforeUnmount() {
    window.Vernql?.destroy()
  }
}
</script>
```

### WordPress

Add this to your theme's `functions.php`:

```php
function add_vernql_widget() {
    ?>
    <script src="https://cdn.vernql.com/widget.js"></script>
    <script>
        Vernql.init({
            apiKey: '<?php echo get_option('vernql_api_key'); ?>',
            schemaId: '<?php echo get_option('vernql_schema_id'); ?>',
            theme: 'auto',
            position: 'bottom-right'
        })
    </script>
    <?php
}
add_action('wp_footer', 'add_vernql_widget');
```

### Angular

```typescript
import { Component, OnInit, OnDestroy } from '@angular/core'

@Component({
  selector: 'app-root',
  template: '<div>My App</div>'
})
export class AppComponent implements OnInit, OnDestroy {
  ngOnInit() {
    const script = document.createElement('script')
    script.src = 'https://cdn.vernql.com/widget.js'
    script.onload = () => {
      (window as any).Vernql.init({
        apiKey: environment.vernqlApiKey,
        schemaId: environment.vernqlSchemaId,
        theme: 'auto',
        position: 'bottom-right'
      })
    }
    document.body.appendChild(script)
  }

  ngOnDestroy() {
    (window as any).Vernql?.destroy()
  }
}
```

## API Methods

### `Vernql.init(config)`
Initialize the widget with configuration options.

### `Vernql.open()`
Programmatically open the widget.

```javascript
document.getElementById('help-button').addEventListener('click', () => {
  Vernql.open()
})
```

### `Vernql.close()`
Programmatically close the widget.

```javascript
Vernql.close()
```

### `Vernql.toggle()`
Toggle the widget open/closed state.

```javascript
Vernql.toggle()
```

### `Vernql.destroy()`
Remove the widget from the page completely.

```javascript
Vernql.destroy()
```

## Development

### Prerequisites

- Node.js 18+ and npm

### Setup

```bash
cd widget
npm install
```

### Development Server

```bash
npm run dev
```

The widget will be available at `http://localhost:3001`

### Testing the Widget

Open `http://localhost:3001/test.html` in your browser to see the widget in action.

### Build for Production

```bash
npm run build
```

### Deploy

The widget consists of two parts:

1. **Widget App** (Next.js) - Deploy to Vercel, Netlify, or any hosting platform
2. **Embed Script** (`public/embed.js`) - Host on a CDN

Update the `widgetUrl` in `embed.js` to point to your deployed widget app.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Security

- Widget runs in a sandboxed iframe
- No access to parent page DOM
- API keys are never exposed to the client
- CORS-enabled for cross-origin embedding

## Troubleshooting

### Widget not appearing?

1. Check that both script tags are present
2. Verify API key and schema ID are correct
3. Check browser console for errors
4. Ensure your API endpoint is accessible

### Widget not connecting to API?

1. Verify `apiUrl` is correct
2. Check CORS settings on your API
3. Ensure API is running and accessible
4. Check network tab for failed requests

### Styling conflicts?

The widget is fully isolated in an iframe, so there should be no CSS conflicts. If you see issues, please report them.

## License

Proprietary - Vernql

## Support

For issues or questions:
- GitHub: https://github.com/your-org/vernql
- Email: support@vernql.com
- Documentation: https://docs.vernql.com
