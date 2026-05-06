/**
 * Vernql Widget Embed Script
 *
 * Usage:
 * <script src="https://your-domain.com/embed.js"></script>
 * <script>
 *   Vernql.init({
 *     apiKey: 'your-api-key',
 *     schemaId: 'your-schema-id',
 *     apiUrl: 'https://api.vernql.com', // optional
 *     theme: 'auto', // 'light' | 'dark' | 'auto'
 *     position: 'bottom-right', // 'bottom-right' | 'bottom-left'
 *     title: 'SQL Assistant', // optional custom title
 *     placeholder: 'Ask a question...', // optional custom placeholder
 *   })
 * </script>
 */

(function() {
  'use strict';

  // Prevent multiple initializations
  if (window.Vernql) {
    console.warn('Vernql widget already initialized');
    return;
  }

  // Default configuration
  const DEFAULT_CONFIG = {
    apiUrl: 'http://localhost:8000',
    theme: 'auto',
    position: 'bottom-right',
    widgetUrl: 'http://localhost:3001', // Change to production URL when deploying
    width: '400px',
    height: '600px',
    // Proxy mode — when set, the widget postMessages queries to this page
    // and this script fetches proxyUrl (same-origin) and replies to the iframe.
    proxyUrl: null,
  };

  // Widget state
  let widgetState = {
    isOpen: false,
    isMinimized: true,
    config: null,
    container: null,
    iframe: null,
    button: null,
    styleEl: null,   // reference so destroy() can clean it up
  };

  /**
   * Create floating button
   */
  function createButton() {
    const button = document.createElement('button');
    button.id = 'vernql-widget-button';
    button.setAttribute('aria-label', 'Open Vernql Assistant');

    const isBottomRight = widgetState.config.position === 'bottom-right';

    button.style.cssText = `
      position: fixed;
      ${isBottomRight ? 'right: 20px' : 'left: 20px'};
      bottom: 20px;
      width: 56px;
      height: 56px;
      border-radius: 28px;
      background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
      border: none;
      box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
      cursor: pointer;
      z-index: 999999;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s ease;
      outline: none;
    `;
    // Restore a visible focus ring for keyboard navigation
    button.addEventListener('focus', function() {
      button.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.6)';
    });
    button.addEventListener('blur', function() {
      button.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.4)';
    });

    // Add SVG icon
    button.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
    `;

    // Hover effect
    button.addEventListener('mouseenter', function() {
      button.style.transform = 'scale(1.05)';
      button.style.boxShadow = '0 6px 16px rgba(59, 130, 246, 0.5)';
    });

    button.addEventListener('mouseleave', function() {
      button.style.transform = 'scale(1)';
      button.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.4)';
    });

    // Click handler
    button.addEventListener('click', toggleWidget);

    document.body.appendChild(button);
    return button;
  }

  /**
   * Create widget container
   */
  function createContainer() {
    const container = document.createElement('div');
    container.id = 'vernql-widget-container';

    const isBottomRight = widgetState.config.position === 'bottom-right';

    container.style.cssText = `
      position: fixed;
      ${isBottomRight ? 'right: 20px' : 'left: 20px'};
      bottom: 90px;
      width: ${widgetState.config.width};
      height: ${widgetState.config.height};
      border-radius: 16px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
      z-index: 999998;
      display: none;
      overflow: hidden;
      background: white;
      animation: vernql-slide-up 0.3s ease-out;
    `;

    // Add slide-up animation (stored so destroy() can remove it)
    const style = document.createElement('style');
    style.id = 'vernql-widget-styles';
    style.textContent = `
      @keyframes vernql-slide-up {
        from { opacity: 0; transform: translateY(20px); }
        to   { opacity: 1; transform: translateY(0); }
      }
      @media (max-width: 520px) {
        #vernql-widget-container {
          width: calc(100vw - 32px) !important;
          height: calc(100dvh - 112px) !important;
          right: 16px !important;
          left: 16px !important;
          bottom: 80px !important;
        }
      }
    `;
    document.head.appendChild(style);
    widgetState.styleEl = style;

    document.body.appendChild(container);
    return container;
  }

  /**
   * Create iframe with widget
   */
  function createIframe() {
    const iframe = document.createElement('iframe');
    iframe.id = 'vernql-widget-iframe';

    // Build widget URL with configuration.
    // Proxy mode: only proxyUrl is sent — apiKey/schemaId stay server-side.
    // Direct mode: apiKey + schemaId are required.
    const params = new URLSearchParams({ theme: widgetState.config.theme });

    if (widgetState.config.proxyUrl) {
      params.append('proxyUrl', widgetState.config.proxyUrl);
    } else {
      params.append('apiKey',   widgetState.config.apiKey);
      params.append('schemaId', widgetState.config.schemaId);
      params.append('apiUrl',   widgetState.config.apiUrl);
    }

    if (widgetState.config.title) {
      params.append('title', widgetState.config.title);
    }

    if (widgetState.config.placeholder) {
      params.append('placeholder', widgetState.config.placeholder);
    }

    iframe.src = `${widgetState.config.widgetUrl}?${params.toString()}`;
    iframe.style.cssText = `
      width: 100%;
      height: 100%;
      border: none;
      border-radius: 16px;
    `;

    iframe.setAttribute('sandbox', 'allow-scripts allow-same-origin allow-forms allow-popups');
    iframe.setAttribute('allow', 'clipboard-write');

    return iframe;
  }

  /**
   * Toggle widget open/close
   */
  function toggleWidget() {
    if (widgetState.isMinimized) {
      openWidget();
    } else {
      closeWidget();
    }
  }

  /**
   * Open widget
   */
  function openWidget() {
    if (!widgetState.container || !widgetState.iframe) {
      console.error('Vernql widget not properly initialized');
      return;
    }

    widgetState.container.style.display = 'block';
    widgetState.isMinimized = false;
    widgetState.isOpen = true;

    // Update button icon to close
    widgetState.button.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"></line>
        <line x1="6" y1="6" x2="18" y2="18"></line>
      </svg>
    `;
  }

  /**
   * Close widget
   */
  function closeWidget() {
    if (!widgetState.container) {
      console.error('Vernql widget not properly initialized');
      return;
    }

    widgetState.container.style.display = 'none';
    widgetState.isMinimized = true;
    widgetState.isOpen = false;

    // Update button icon to chat
    widgetState.button.innerHTML = `
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
      </svg>
    `;
  }

  /**
   * Proxy mode — listen for 'vernql:query' messages from the iframe,
   * fetch the host page's proxy endpoint (same-origin, no CORS needed),
   * and postMessage the result back to the iframe.
   */
  function setupProxyMessaging() {
    if (!widgetState.config.proxyUrl) return;

    window.addEventListener('message', async function(event) {
      // Security: only handle messages from our own iframe
      if (!widgetState.iframe || event.source !== widgetState.iframe.contentWindow) return;
      if (!event.data || event.data.type !== 'vernql:query') return;

      var question  = event.data.question;
      var messageId = event.data.messageId;

      try {
        var response = await fetch(widgetState.config.proxyUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question: question }),
        });

        if (!response.ok) {
          throw new Error('Proxy request failed with status ' + response.status);
        }

        var data = await response.json();

        // Target the widget's own origin so other scripts on the page
        // cannot intercept the result data.
        var iframeOrigin = new URL(widgetState.config.widgetUrl).origin;
        widgetState.iframe.contentWindow.postMessage({
          type: 'vernql:result',
          messageId: messageId,
          visualization: data.visualization,
        }, iframeOrigin);
      } catch (err) {
        var iframeOrigin2 = new URL(widgetState.config.widgetUrl).origin;
        widgetState.iframe.contentWindow.postMessage({
          type: 'vernql:error',
          messageId: messageId,
          error: err.message || 'Unknown error',
        }, iframeOrigin2);
      }
    });
  }

  /**
   * Initialize widget
   */
  function init(config) {
    // Validate required config — either proxyUrl (proxy mode) or apiKey+schemaId (direct mode)
    if (!config) {
      console.error('Vernql widget: config is required');
      return;
    }
    if (!config.proxyUrl && (!config.apiKey || !config.schemaId)) {
      console.error('Vernql widget: provide either proxyUrl (proxy mode) or apiKey + schemaId (direct mode)');
      return;
    }

    // Merge with defaults
    widgetState.config = Object.assign({}, DEFAULT_CONFIG, config);

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function() {
        initializeWidget();
      });
    } else {
      initializeWidget();
    }
  }

  /**
   * Initialize widget elements
   */
  function initializeWidget() {
    try {
      // Create UI elements
      widgetState.button = createButton();
      widgetState.container = createContainer();
      widgetState.iframe = createIframe();

      // Append iframe to container
      widgetState.container.appendChild(widgetState.iframe);

      // Proxy mode: wire up the postMessage relay between iframe and host page
      setupProxyMessaging();

      console.log('Vernql widget initialized successfully');
    } catch (error) {
      console.error('Failed to initialize Vernql widget:', error);
    }
  }

  /**
   * Destroy widget
   */
  function destroy() {
    if (widgetState.container) widgetState.container.remove();
    if (widgetState.button)    widgetState.button.remove();
    if (widgetState.styleEl)   widgetState.styleEl.remove();
    widgetState = {
      isOpen: false,
      isMinimized: true,
      config: null,
      container: null,
      iframe: null,
      button: null,
      styleEl: null,
    };
    // Allow re-initialization after destroy
    delete window.Vernql;
  }

  // Expose public API
  window.Vernql = {
    init: init,
    open: openWidget,
    close: closeWidget,
    toggle: toggleWidget,
    destroy: destroy,
    version: '1.0.0',
  };

  console.log('Vernql widget loader ready (v1.0.0)');
})();
